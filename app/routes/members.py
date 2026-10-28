from io import BytesIO
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
    return render_template("members/detail.html",
                           member=member, breakdown=breakdown,
                           txns=txns, loans=loans, guarantees=guarantees)


@members_bp.route("/export.xlsx")
@login_required
def export_xlsx():
    members = Member.query.order_by(Member.member_number).all()
    data = [{
        "Member No": m.member_number,
        "Full Name": m.full_name,
        "Phone": m.phone,
        "Join Date": m.join_date.isoformat() if m.join_date else "",
        "Savings (KES)": float(m.savings_balance or 0),
        "Shares": m.shares,
        "Trust Score": m.trust_score,
        "Rank": m.default_rank,
        "Status": m.status,
    } for m in members]
    df = pd.DataFrame(data)
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Members")
    out.seek(0)
    return send_file(
        out,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="sacco_members.xlsx",
    )
