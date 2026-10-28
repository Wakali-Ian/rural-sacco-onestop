from datetime import date
from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template
from app.models import db
from app.models.member import Member
from app.models.mpesa import MpesaTransaction
from app.models.loan import Loan
from app.models.risk import RiskEvent
from app.models.transaction import Transaction
from app.services.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    total_members = Member.query.filter_by(status="active").count()
    total_savings = float(db.session.query(
        db.func.coalesce(db.func.sum(Member.savings_balance), 0)
    ).scalar() or 0)
    total_loan_book = float(db.session.query(
        db.func.coalesce(db.func.sum(Loan.outstanding_balance), 0)
    ).filter(Loan.status.in_(["active", "disbursed", "overdue"])).scalar() or 0)

    mpesa_total = MpesaTransaction.query.count()
    mpesa_matched = MpesaTransaction.query.filter_by(status="matched").count()
    unmatched_count = mpesa_total - mpesa_matched
    match_rate = (100.0 * mpesa_matched / mpesa_total) if mpesa_total else 0.0

    rank_dist = {r: 0 for r in "ABCDE"}
    for (rank,) in db.session.query(Member.default_rank).filter_by(status="active"):
        if rank in rank_dist:
            rank_dist[rank] += 1

    risk_sev = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for (sev,) in db.session.query(RiskEvent.severity).filter_by(status="open"):
        if sev in risk_sev:
            risk_sev[sev] += 1

    today = date.today()
    first = today.replace(day=1) - relativedelta(months=11)
    months, cur = [], first
    for _ in range(12):
        months.append(cur)
        cur += relativedelta(months=1)
    keys = [m.strftime("%Y-%m") for m in months]
    month_labels = [m.strftime("%b") for m in months]
    dep = {k: 0.0 for k in keys}
    wd = {k: 0.0 for k in keys}
    for txn in Transaction.query.filter(Transaction.created_at >= first).all():
        key = txn.created_at.strftime("%Y-%m")
        if key not in dep:
            continue
        if txn.type == "deposit":
            dep[key] += float(txn.amount)
        elif txn.type == "withdrawal":
            wd[key] += float(txn.amount)

    aging = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
    active_loans = Loan.query.filter(
        Loan.status.in_(["active", "disbursed", "overdue"]),
        Loan.outstanding_balance > 0, Loan.due_date.isnot(None),
    ).all()
    for l in active_loans:
        days = (today - l.due_date).days
        if days <= 0:
            continue
        amt = float(l.outstanding_balance or 0)
        if days <= 30: aging["0-30"] += amt
        elif days <= 60: aging["31-60"] += amt
        elif days <= 90: aging["61-90"] += amt
        else: aging["90+"] += amt

    recent_mpesa = (MpesaTransaction.query
                    .order_by(MpesaTransaction.created_at.desc()).limit(10).all())
    open_risks = (RiskEvent.query.filter_by(status="open")
                  .order_by(RiskEvent.created_at.desc()).limit(8).all())
    overdue = (Loan.query
               .filter(Loan.status.in_(["active", "disbursed", "overdue"]),
                       Loan.due_date < today, Loan.outstanding_balance > 0)
               .order_by(Loan.due_date.asc()).limit(8).all())

    return render_template(
        "dashboard/index.html",
        total_members=total_members, total_savings=total_savings,
        total_loan_book=total_loan_book, match_rate=match_rate,
        mpesa_matched=mpesa_matched, unmatched_count=unmatched_count,
        rank_dist=rank_dist, risk_sev=risk_sev,
        month_labels=month_labels,
        deposits=[round(dep[k], 2) for k in keys],
        withdrawals=[round(wd[k], 2) for k in keys],
        aging=aging, recent_mpesa=recent_mpesa,
        open_risks=open_risks, overdue=overdue,
    )
