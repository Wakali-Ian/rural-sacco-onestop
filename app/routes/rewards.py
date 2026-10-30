from flask import Blueprint, render_template
from app.services.auth import login_required
from app.services.rewards_engine import leaderboard
from app.models.sacco_settings import SaccoSettings

rewards_bp = Blueprint("rewards", __name__, url_prefix="/rewards")


@rewards_bp.route("/")
@login_required
def index():
    data = leaderboard(limit=10)
    settings = SaccoSettings.get()
    return render_template("rewards/leaderboard.html", settings=settings, **data)
