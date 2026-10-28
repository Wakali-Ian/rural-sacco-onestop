from datetime import date
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

    recent_mpesa = (MpesaTransaction.query
                    .order_by(MpesaTransaction.created_at.desc())
                    .limit(15).all())
    open_risks = (RiskEvent.query.filter_by(status="open")
                  .order_by(RiskEvent.created_at.desc()).limit(10).all())

    today = date.today()
    overdue = (Loan.query
               .filter(Loan.status.in_(["active", "disbursed", "overdue"]),
                       Loan.due_date < today,
                       Loan.outstanding_balance > 0)
               .order_by(Loan.due_date.asc()).limit(10).all())

    return render_template("dashboard/index.html",
                           total_members=total_members,
                           total_savings=total_savings,
                           total_loan_book=total_loan_book,
                           match_rate=match_rate,
                           unmatched_count=unmatched_count,
                           recent_mpesa=recent_mpesa,
                           open_risks=open_risks,
                           overdue=overdue)
