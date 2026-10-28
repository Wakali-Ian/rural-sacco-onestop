"""Automated risk checks. Produces / updates RiskEvent rows."""
from datetime import date, datetime, timedelta
from app.models import db
from app.models.member import Member
from app.models.loan import Loan
from app.models.guarantor import Guarantor
from app.models.transaction import Transaction
from app.models.risk import RiskEvent


def _upsert(risk_type, severity, description, member_id=None, loan_id=None,
            mitigation=None):
    q = RiskEvent.query.filter_by(risk_type=risk_type, status="open")
    if member_id is not None:
        q = q.filter_by(member_id=member_id)
    if loan_id is not None:
        q = q.filter_by(loan_id=loan_id)
    event = q.first()
    if event:
        event.severity = severity
        event.description = description
        event.mitigation = mitigation
        event.created_at = datetime.utcnow()
    else:
        db.session.add(RiskEvent(
            risk_type=risk_type, severity=severity, description=description,
            member_id=member_id, loan_id=loan_id, mitigation=mitigation,
            status="open",
        ))
    return True


def _close_stale(risk_type, keep_member_ids=(), keep_loan_ids=()):
    q = RiskEvent.query.filter_by(risk_type=risk_type, status="open")
    if keep_member_ids:
        q = q.filter(~RiskEvent.member_id.in_(keep_member_ids))
    if keep_loan_ids:
        q = q.filter(~RiskEvent.loan_id.in_(keep_loan_ids))
    for ev in q.all():
        ev.status = "resolved"
        ev.resolved_at = datetime.utcnow()


def check_liquidity():
    total_savings = db.session.query(db.func.coalesce(db.func.sum(Member.savings_balance), 0)).scalar() or 0
    total_outstanding = (db.session.query(db.func.coalesce(db.func.sum(Loan.outstanding_balance), 0))
                         .filter(Loan.status.in_(["active", "disbursed", "overdue"])).scalar() or 0)
    total_savings, total_outstanding = float(total_savings), float(total_outstanding)
    if total_savings == 0:
        return 0
    ratio = total_outstanding / total_savings
    if ratio >= 0.85:
        _upsert("liquidity", "critical",
                f"Loan/savings ratio {ratio*100:.1f}% exceeds 85% critical",
                mitigation="Pause new approvals; push deposit mobilisation.")
        return 1
    if ratio >= 0.70:
        _upsert("liquidity", "high",
                f"Loan/savings ratio {ratio*100:.1f}% exceeds 70% warning",
                mitigation="Monitor closely; limit large new loans.")
        return 1
    _close_stale("liquidity")
    return 0


def check_concentration():
    active = Loan.query.filter(Loan.status.in_(["active", "disbursed", "overdue"])).all()
    total_book = sum(float(l.outstanding_balance or 0) for l in active)
    if total_book == 0:
        _close_stale("concentration")
        return 0
    keep_loan_ids = []
    for loan in active:
        share = float(loan.outstanding_balance or 0) / total_book
        if share >= 0.30:
            keep_loan_ids.append(loan.id)
            _upsert("concentration", "high",
                    f"Loan {loan.loan_number} is {share*100:.1f}% of book",
                    member_id=loan.member_id, loan_id=loan.id,
                    mitigation="Cap single-borrower exposure.")
        elif share >= 0.20:
            keep_loan_ids.append(loan.id)
            _upsert("concentration", "medium",
                    f"Loan {loan.loan_number} is {share*100:.1f}% of book",
                    member_id=loan.member_id, loan_id=loan.id,
                    mitigation="Flag for committee review.")
    _close_stale("concentration", keep_loan_ids=keep_loan_ids)
    return len(keep_loan_ids)


def check_member_defaults():
    risky = Member.query.filter(Member.status == "active", Member.trust_score < 40).all()
    keep = []
    for m in risky:
        keep.append(m.id)
        _upsert("member_default", "high",
                f"{m.full_name} ({m.member_number}) trust score {m.trust_score:.1f} < 40",
                member_id=m.id,
                mitigation="Suspend new loans; require guarantors.")
    _close_stale("member_default", keep_member_ids=keep)
    return len(keep)


def check_guarantor_exposure():
    rows = (db.session.query(Guarantor.guarantor_member_id,
                             db.func.sum(Guarantor.amount_guaranteed))
            .filter(Guarantor.status == "active")
            .group_by(Guarantor.guarantor_member_id).all())
    keep = []
    for member_id, total_g in rows:
        member = Member.query.get(member_id)
        if not member:
            continue
        savings = float(member.savings_balance or 0)
        if savings <= 0:
            continue
        exposure = float(total_g) / savings
        if exposure >= 0.50:
            keep.append(member_id)
            _upsert("guarantor_exposure", "high",
                    f"{member.full_name} guarantees KES {float(total_g):,.0f} = {exposure*100:.0f}% of savings",
                    member_id=member_id,
                    mitigation="Require additional guarantor.")
        elif exposure >= 0.30:
            keep.append(member_id)
            _upsert("guarantor_exposure", "medium",
                    f"{member.full_name} guarantees KES {float(total_g):,.0f} = {exposure*100:.0f}% of savings",
                    member_id=member_id,
                    mitigation="Monitor; avoid new guarantees.")
    _close_stale("guarantor_exposure", keep_member_ids=keep)
    return len(keep)


def check_overdue_aging(today=None):
    today = today or date.today()
    active = Loan.query.filter(Loan.status.in_(["active", "disbursed", "overdue"]),
                               Loan.due_date != None).all()
    keep_loan_ids = []
    for loan in active:
        days = (today - loan.due_date).days
        if days <= 0:
            continue
        keep_loan_ids.append(loan.id)
        if days >= 90:
            sev = "critical"
        elif days >= 60:
            sev = "high"
        elif days >= 30:
            sev = "medium"
        else:
            continue
        _upsert("overdue_aging", sev,
                f"Loan {loan.loan_number} overdue {days} days (outstanding KES {float(loan.outstanding_balance or 0):,.0f})",
                member_id=loan.member_id, loan_id=loan.id,
                mitigation="Trigger penalties; contact member + guarantors.")
    _close_stale("overdue_aging", keep_loan_ids=keep_loan_ids)
    return len(keep_loan_ids)


def check_delinquency_rate(today=None):
    today = today or date.today()
    active = Loan.query.filter(Loan.status.in_(["active", "disbursed", "overdue"])).all()
    if not active:
        _close_stale("delinquency")
        return 0
    overdue = [l for l in active if l.due_date and l.due_date < today
               and float(l.outstanding_balance or 0) > 0]
    rate = len(overdue) / len(active)
    if rate >= 0.20:
        _upsert("delinquency", "critical",
                f"Portfolio delinquency {rate*100:.1f}% exceeds 20%",
                mitigation="Escalate to board; review credit policy.")
        return 1
    if rate >= 0.10:
        _upsert("delinquency", "high",
                f"Portfolio delinquency {rate*100:.1f}% exceeds 10%",
                mitigation="Tighten new-loan approvals.")
        return 1
    _close_stale("delinquency")
    return 0


def check_fraud_patterns(today=None):
    today = today or date.today()
    window_start = datetime.combine(today, datetime.min.time()) - timedelta(hours=24)
    rows = (db.session.query(Transaction.member_id, Transaction.type,
                             db.func.count(Transaction.id))
            .filter(Transaction.created_at >= window_start)
            .group_by(Transaction.member_id, Transaction.type).all())
    by_member = {}
    for mid, typ, cnt in rows:
        by_member.setdefault(mid, {})[typ] = cnt
    keep = []
    for mid, counts in by_member.items():
        if counts.get("deposit", 0) >= 5 and counts.get("withdrawal", 0) >= 5:
            keep.append(mid)
            member = Member.query.get(mid)
            _upsert("fraud_pattern", "high",
                    f"{member.full_name}: {counts['deposit']} deposits + {counts['withdrawal']} withdrawals in 24h",
                    member_id=mid,
                    mitigation="Freeze account for review.")
    _close_stale("fraud_pattern", keep_member_ids=keep)
    return len(keep)


def run_all_checks(today=None):
    return {
        "liquidity":          check_liquidity(),
        "concentration":      check_concentration(),
        "member_default":     check_member_defaults(),
        "guarantor_exposure": check_guarantor_exposure(),
        "overdue_aging":      check_overdue_aging(today),
        "delinquency":        check_delinquency_rate(today),
        "fraud_pattern":      check_fraud_patterns(today),
    }
