from io import BytesIO
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
from flask import Blueprint, render_template, request, send_file
from app.models import db
from app.models.member import Member
from app.models.transaction import Transaction
from app.models.loan import Loan
from app.models.guarantor import Guarantor
from app.services.auth import login_required
from app.services.credit_scoring import score_member

members_bp = Blueprint("members", __name__, url_prefix="/members")


@members_bp.route("/")
@login_required
def list_members():
    q = request.args.get("q", "").strip()
    query = Member.query
    if q:
        query = query.filter(db.or_(
            Member.full_name.ilike(f"%{q}%"),
            Member.member_number.ilike(f"%{q}%"),
            Member.phone.ilike(f"%{q}%"),
        ))
    members = query.order_by(Member.member_number).all()
    return render_template("members/list.html", members=members, q=q)


@members_bp.route("/<int:member_id>")
@login_required
def detail(member_id):
    member = Member.query.get_or_404(member_id)
    breakdown = score_member(member_id, persist=False)
    txns = (Transaction.query.filter_by(member_id=member_id)
            .order_by(Transaction.created_at.desc()).limit(20).all())
    loans = (Loan.query.filter_by(member_id=member_id)
             .order_by(Loan.created_at.desc()).all())
    guarantees = Guarantor.query.filter_by(guarantor_member_id=member_id).all()

    radar_labels = [k.replace("_", " ").title() for k in breakdown["breakdown"].keys()]
    radar_scores = [round((v["score"] / v["max"] * 100), 1) if v["max"] else 0
                    for v in breakdown["breakdown"].values()]

    today = date.today()
    first = today.replace(day=1) - relativedelta(months=5)
    months, cur = [], first
    for _ in range(6):
        months.append(cur)
        cur += relativedelta(months=1)
    keys = [m.strftime("%Y-%m") for m in months]
    month_labels = [m.strftime("%b") for m in months]
    dep = {k: 0.0 for k in keys}
    wd = {k: 0.0 for k in keys}
    for txn in (Transaction.query
                .filter(Transaction.member_id == member_id,
                        Transaction.created_at >= first).all()):
        key = txn.created_at.strftime("%Y-%m")
        if key not in dep:
            continue
        if txn.type == "deposit":
            dep[key] += float(txn.amount)
        elif txn.type == "withdrawal":
            wd[key] += float(txn.amount)

    return render_template("members/detail.html",
                           member=member, breakdown=breakdown,
                           txns=txns, loans=loans, guarantees=guarantees,
                           radar_labels=radar_labels, radar_scores=radar_scores,
                           month_labels=month_labels,
                           deposits=[round(dep[k], 2) for k in keys],
                           withdrawals=[round(wd[k], 2) for k in keys])


@members_bp.route("/export.xlsx")
@login_required
def export_xlsx():
    members = Member.query.order_by(Member.member_number).all()
    data = [{"Member No": m.member_number, "Full Name": m.full_name,
             "Phone": m.phone,
             "Join Date": m.join_date.isoformat() if m.join_date else "",
             "Savings (KES)": float(m.savings_balance or 0),
             "Shares": m.shares, "Trust Score": m.trust_score,
             "Rank": m.default_rank, "Status": m.status} for m in members]
    df = pd.DataFrame(data)
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Members")
    out.seek(0)
    return send_file(out,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True, download_name="sacco_members.xlsx")
