import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db
from app.models.sacco_settings import SaccoSettings
from app.services.auth import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/settings", methods=["GET", "POST"])
@role_required("admin")
def settings():
    s = SaccoSettings.get()
    if request.method == "POST":
        try:
            s.sacco_name = (request.form.get("sacco_name") or "").strip()[:120]
            s.share_value = float(request.form.get("share_value") or 100)
            s.dividend_rate = float(request.form.get("dividend_rate") or 0.15)
            s.savings_interest_base = float(request.form.get("savings_interest_base") or 0.005)
            s.bonus_rate_savings = float(request.form.get("bonus_rate_savings") or 0.01)
            s.reward_points_per_100_kes = int(request.form.get("reward_points_per_100_kes") or 1)
            s.streak_bonus_kes = float(request.form.get("streak_bonus_kes") or 500)
            s.referral_bonus_kes = float(request.form.get("referral_bonus_kes") or 200)
            s.tier_silver = int(request.form.get("tier_silver") or 50)
            s.tier_gold = int(request.form.get("tier_gold") or 200)
            s.tier_platinum = int(request.form.get("tier_platinum") or 500)
            s.min_monthly_deposit = float(request.form.get("min_monthly_deposit") or 100)
            tiers = []
            for i in range(4):
                tiers.append({
                    "min_balance": float(request.form.get(f"tier_{i}_min") or 0),
                    "bonus_rate":  float(request.form.get(f"tier_{i}_rate") or 0),
                })
            s.bonus_tiers = json.dumps(tiers)
            db.session.commit()
            flash("Settings saved.", "success")
            return redirect(url_for("admin.settings"))
        except (ValueError, TypeError) as e:
            db.session.rollback()
            flash(f"Invalid input: {e}", "danger")
    tiers = json.loads(s.bonus_tiers or "[]")
    while len(tiers) < 4:
        tiers.append({"min_balance": 0, "bonus_rate": 0})
    return render_template("admin/settings.html", s=s, tiers=tiers)
