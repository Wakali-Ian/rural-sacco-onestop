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
from app.services.auth import login_required, role_required
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
    from app.models.etims import EtimsReceipt
    txns = (Transaction.query.filter_by(member_id=member_id)
            .order_by(Transaction.created_at.desc()).limit(20).all())
    receipts = {r.transaction_id: r for r in
                EtimsReceipt.query.filter(
                    EtimsReceipt.transaction_id.in_([t.id for t in txns])).all()}
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

    from app.services.rewards_engine import get_or_create_account, bonus_for_member, next_tier
    from app.models.sacco_settings import SaccoSettings
    account = get_or_create_account(member.id)
    settings = SaccoSettings.get()
    bonus = bonus_for_member(member, account, settings)
    nxt = next_tier(member, account, settings)
    return render_template("members/detail.html",
                           member=member, breakdown=breakdown,
                           account=account, settings=settings,
                           bonus=bonus, next_tier=nxt,
                           txns=txns, loans=loans, guarantees=guarantees,
                           receipts=receipts,
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


@members_bp.route("/new", methods=["GET", "POST"])
@role_required("admin", "treasurer")
def new_member():
    from datetime import datetime
    from flask import flash, redirect, url_for
    from app.services.validators import validate_member_form, next_member_number
    errors, form = {}, {}
    if request.method == "POST":
        errors, cleaned = validate_member_form(request.form, member_id=None)
        form = dict(request.form)
        if not errors:
            m = Member(
                member_number=cleaned["member_number"],
                full_name=cleaned["full_name"],
                phone=cleaned["phone"],
                national_id=cleaned.get("national_id"),
                join_date=cleaned["join_date"],
                shares=cleaned["shares"],
                language_preference=cleaned["language_preference"],
                consent_given=cleaned["consent_given"],
                status="active",
            )
            db.session.add(m)
            db.session.commit()
            flash(f"Member {m.member_number} created.", "success")
            return redirect(url_for("members.detail", member_id=m.id))
    if not form:
        form = {
            "member_number": next_member_number(),
            "join_date": datetime.utcnow().date().isoformat(),
            "language_preference": "sw",
            "shares": "0",
        }
    return render_template("members/form.html",
                           form=form, errors=errors, member=None)


@members_bp.route("/<int:member_id>/edit", methods=["GET", "POST"])
@role_required("admin", "treasurer")
def edit_member(member_id):
    from flask import flash, redirect, url_for
    from app.services.validators import validate_member_form
    member = Member.query.get_or_404(member_id)
    errors = {}
    if request.method == "POST":
        errors, cleaned = validate_member_form(request.form, member_id=member_id)
        if not errors:
            member.full_name = cleaned["full_name"]
            member.phone = cleaned["phone"]
            member.national_id = cleaned.get("national_id")
            member.join_date = cleaned["join_date"]
            member.shares = cleaned["shares"]
            member.language_preference = cleaned["language_preference"]
            member.consent_given = cleaned["consent_given"]
            db.session.commit()
            flash("Member updated.", "success")
            return redirect(url_for("members.detail", member_id=member.id))
        form = dict(request.form)
    else:
        form = {
            "member_number": member.member_number,
            "full_name": member.full_name,
            "phone": member.phone,
            "national_id": member.national_id or "",
            "join_date": member.join_date.isoformat() if member.join_date else "",
            "shares": str(member.shares or 0),
            "language_preference": member.language_preference or "sw",
            "consent_given": "on" if member.consent_given else "",
        }
    return render_template("members/form.html",
                           form=form, errors=errors, member=member)


@members_bp.route("/<int:member_id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_status(member_id):
    from flask import flash, redirect, url_for
    member = Member.query.get_or_404(member_id)
    if member.status == "active":
        member.status = "inactive"
        msg = f"Member {member.member_number} deactivated."
    else:
        member.status = "active"
        msg = f"Member {member.member_number} reactivated."
    db.session.commit()
    flash(msg, "success")
    return redirect(url_for("members.detail", member_id=member.id))
