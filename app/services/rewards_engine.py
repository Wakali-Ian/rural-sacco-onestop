"""Points, tiers, streaks, and annual savings bonus."""
import json
from datetime import date
from dateutil.relativedelta import relativedelta
from app.models import db
from app.models.member import Member
from app.models.transaction import Transaction
from app.models.reward import RewardAccount, RewardTransaction
from app.models.sacco_settings import SaccoSettings


def get_or_create_account(member_id):
    acct = RewardAccount.query.filter_by(member_id=member_id).first()
    if not acct:
        acct = RewardAccount(member_id=member_id)
        db.session.add(acct)
        db.session.commit()
    return acct


def compute_points(member, settings):
    total = (db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0))
             .filter(Transaction.member_id == member.id,
                     Transaction.type == "deposit").scalar() or 0)
    return int(float(total) / 100 * settings.reward_points_per_100_kes)


def compute_streak(member):
    rows = (db.session.query(Transaction.created_at)
            .filter(Transaction.member_id == member.id,
                    Transaction.type == "deposit").all())
    months = {r[0].strftime("%Y-%m") for r in rows if r[0]}
    streak, cursor = 0, date.today()
    for _ in range(24):
        if cursor.strftime("%Y-%m") in months:
            streak += 1
            cursor = cursor - relativedelta(months=1)
        else:
            break
    return streak


def tier_from_points(points, settings):
    if points >= settings.tier_platinum: return "platinum"
    if points >= settings.tier_gold: return "gold"
    if points >= settings.tier_silver: return "silver"
    return "bronze"


def bonus_rate_for_balance(balance, settings):
    tiers = json.loads(settings.bonus_tiers or "[]")
    rate = float(settings.savings_interest_base or 0)
    for t in tiers:
        if balance >= t["min_balance"]:
            rate = t["bonus_rate"]
    return rate


def bonus_for_member(member, account, settings):
    savings = float(member.savings_balance or 0)
    rate = bonus_rate_for_balance(savings, settings)
    savings_bonus = round(savings * rate, 2)
    streak_bonus = float(settings.streak_bonus_kes or 0) if account.streak_months >= 12 else 0.0
    return {
        "savings_balance": savings,
        "rate": rate,
        "savings_bonus": savings_bonus,
        "streak_bonus": streak_bonus,
        "total": round(savings_bonus + streak_bonus, 2),
        "streak_months": account.streak_months,
        "points": account.points,
        "tier": account.tier,
    }


def next_tier(member, account, settings):
    if account.tier == "platinum":
        return None
    thresholds = {"bronze": settings.tier_silver, "silver": settings.tier_gold, "gold": settings.tier_platinum}
    target = thresholds.get(account.tier)
    return {"next_tier": {"bronze":"silver","silver":"gold","gold":"platinum"}[account.tier],
            "points_needed": max(0, target - account.points)}


def recompute_all():
    settings = SaccoSettings.get()
    processed = 0
    for member in Member.query.filter_by(status="active").all():
        acct = get_or_create_account(member.id)
        acct.points = compute_points(member, settings)
        acct.streak_months = compute_streak(member)
        acct.tier = tier_from_points(acct.points, settings)
        processed += 1
    db.session.commit()
    return {"processed": processed}


def apply_annual_bonus(year, credit_to_savings=True):
    settings = SaccoSettings.get()
    posted, total_kes = 0, 0.0
    for member in Member.query.filter_by(status="active").all():
        acct = get_or_create_account(member.id)
        if acct.last_bonus_year == year:
            continue
        b = bonus_for_member(member, acct, settings)
        if b["total"] <= 0:
            continue
        reason = f"Annual bonus {year}: savings×{b['rate']*100:.2f}% + streak"
        db.session.add(RewardTransaction(
            member_id=member.id, type="annual_bonus",
            kes_delta=b["total"], reason=reason,
        ))
        if credit_to_savings:
            member.savings_balance = float(member.savings_balance or 0) + b["total"]
            db.session.add(Transaction(
                member_id=member.id, type="deposit", amount=b["total"],
                balance_after=member.savings_balance,
                reference=f"BONUS-{year}-{member.id}",
                channel="bonus", created_by="system",
                notes=reason,
            ))
        acct.total_bonus_earned = float(acct.total_bonus_earned or 0) + b["total"]
        acct.last_bonus_year = year
        posted += 1
        total_kes += b["total"]
    db.session.commit()
    return {"posted": posted, "total_kes": round(total_kes, 2)}


def leaderboard(limit=10):
    rows = (db.session.query(Member, RewardAccount)
            .join(RewardAccount, RewardAccount.member_id == Member.id)
            .filter(Member.status == "active"))
    by_points = rows.order_by(RewardAccount.points.desc()).limit(limit).all()
    by_streak = rows.order_by(RewardAccount.streak_months.desc(),
                              RewardAccount.points.desc()).limit(limit).all()
    tier_counts = {t: 0 for t in ("bronze", "silver", "gold", "platinum")}
    for (tier,) in db.session.query(RewardAccount.tier).all():
        if tier in tier_counts:
            tier_counts[tier] += 1
    return {"by_points": by_points, "by_streak": by_streak, "tier_counts": tier_counts}
