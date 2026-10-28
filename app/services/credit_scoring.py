"""Trust Score (0-100) and Default Rank (A-E) engine."""
from datetime import date, datetime, timedelta
from app.models import db
from app.models.member import Member
from app.models.transaction import Transaction
from app.models.loan import Loan
from app.models.guarantor import Guarantor
from app.models.meeting import Meeting, MeetingAttendance


WEIGHTS = {
    "repayment_history":     40.0,
    "savings_consistency":   20.0,
    "meeting_attendance":    15.0,
    "guarantor_performance": 10.0,
    "membership_tenure":     10.0,
    "group_activity":         5.0,
}

RANK_TABLE = [
    (90, "A", "Excellent",  3.0, 0, 24, 10.0),
    (75, "B", "Good",       2.5, 1, 18, 12.0),
    (60, "C", "Fair",       2.0, 2, 12, 14.0),
    (40, "D", "High Risk",  1.0, 3,  6, 18.0),
    ( 0, "E", "Blacklisted",0.0, 0,  0,  0.0),
]


def rank_from_score(score):
    for min_score, rank, label, mult, guar, term, rate in RANK_TABLE:
        if score >= min_score:
            return {
                "rank": rank, "label": label,
                "max_loan_multiplier": mult,
                "guarantors_required": guar,
                "max_term_months": term,
                "interest_rate": rate,
            }
    return {"rank": "E", "label": "Blacklisted", "max_loan_multiplier": 0.0,
            "guarantors_required": 0, "max_term_months": 0, "interest_rate": 0.0}


def _repayment_score(member, today):
    loans = Loan.query.filter_by(member_id=member.id).all()
    if not loans:
        return WEIGHTS["repayment_history"] * 0.5, "no loan history"
    penalty = 0.0
    repaid = 0
    for loan in loans:
        ob = float(loan.outstanding_balance or 0)
        if loan.status == "defaulted":
            penalty += 20
        elif loan.status in ("active", "disbursed", "overdue") and loan.due_date:
            days = (today - loan.due_date).days
            if days > 0 and ob > 0:
                penalty += min(15, days * 0.3)
        elif loan.status in ("repaid", "closed") or ob == 0:
            repaid += 1
    base = WEIGHTS["repayment_history"] * (repaid / len(loans))
    score = max(0.0, min(WEIGHTS["repayment_history"], base - penalty))
    return score, f"{repaid}/{len(loans)} repaid, penalty -{penalty:.1f}"


def _savings_score(member, today):
    start = today - timedelta(days=365)
    rows = (db.session.query(Transaction.created_at)
            .filter(Transaction.member_id == member.id,
                    Transaction.type == "deposit",
                    Transaction.created_at >= datetime.combine(start, datetime.min.time()))
            .all())
    months = {r[0].strftime("%Y-%m") for r in rows}
    score = WEIGHTS["savings_consistency"] * (len(months) / 12.0)
    return min(WEIGHTS["savings_consistency"], score), f"{len(months)}/12 months active"


def _attendance_score(member, today):
    start = today - timedelta(days=365)
    total = Meeting.query.filter(Meeting.meeting_date >= start).count()
    if total == 0:
        return WEIGHTS["meeting_attendance"] * 0.5, "no meetings (neutral)"
    attended = (MeetingAttendance.query
                .join(Meeting)
                .filter(MeetingAttendance.member_id == member.id,
                        MeetingAttendance.status == "present",
                        Meeting.meeting_date >= start)
                .count())
    score = WEIGHTS["meeting_attendance"] * (attended / total)
    return score, f"{attended}/{total} attended"


def _guarantor_score(member, today):
    given = Guarantor.query.filter_by(guarantor_member_id=member.id).all()
    if not given:
        return WEIGHTS["guarantor_performance"] * 0.75, "no guarantees (neutral)"
    losses = 0
    for g in given:
        loan = Loan.query.get(g.loan_id)
        if loan and loan.status == "defaulted":
            losses += 1
    score = WEIGHTS["guarantor_performance"] * max(0.0, 1.0 - 0.5 * losses)
    return score, f"{len(given)} guarantees, {losses} defaulted"


def _tenure_score(member, today):
    if not member.join_date:
        return 0.0, "no join date"
    months = max(0, (today - member.join_date).days / 30.0)
    score = WEIGHTS["membership_tenure"] * min(1.0, months / 24.0)
    return score, f"{months:.1f} months"


def _activity_score(member, today):
    score = 0.0
    note = []
    if (member.shares or 0) > 0:
        score += 2.5
        note.append("has shares")
    recent = (Transaction.query
              .filter(Transaction.member_id == member.id,
                      Transaction.created_at >= datetime.combine(today - timedelta(days=30), datetime.min.time()))
              .count())
    if recent > 0:
        score += 2.5
        note.append(f"{recent} recent txns")
    return score, ", ".join(note) or "inactive"


def score_member(member_id, today=None, persist=True):
    today = today or date.today()
    member = Member.query.get(member_id)
    if not member:
        return None
    breakdown = {}
    total = 0.0
    for name, fn in [
        ("repayment_history",     _repayment_score),
        ("savings_consistency",   _savings_score),
        ("meeting_attendance",    _attendance_score),
        ("guarantor_performance", _guarantor_score),
        ("membership_tenure",     _tenure_score),
        ("group_activity",        _activity_score),
    ]:
        s, note = fn(member, today)
        breakdown[name] = {"score": round(s, 2), "max": WEIGHTS[name], "note": note}
        total += s
    total = round(min(100.0, max(0.0, total)), 2)
    meta = rank_from_score(total)
    if persist:
        member.trust_score = total
        member.default_rank = meta["rank"]
        db.session.commit()
    return {
        "member_id": member.id,
        "member_number": member.member_number,
        "full_name": member.full_name,
        "trust_score": total,
        "rank": meta["rank"],
        "rank_label": meta["label"],
        "loan_terms": {k: meta[k] for k in
                       ("max_loan_multiplier", "guarantors_required",
                        "max_term_months", "interest_rate")},
        "breakdown": breakdown,
    }


def score_all_members(today=None, persist=True):
    members = Member.query.filter_by(status="active").all()
    return [score_member(m.id, today=today, persist=persist) for m in members]
