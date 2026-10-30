from datetime import datetime
from app.models import db


class SaccoSettings(db.Model):
    __tablename__ = "sacco_settings"
    id = db.Column(db.Integer, primary_key=True)
    sacco_name = db.Column(db.String(120), default="Rural SACCO")
    share_value = db.Column(db.Numeric(12, 2), default=100)

    dividend_rate = db.Column(db.Float, default=0.15)
    savings_interest_base = db.Column(db.Float, default=0.005)
    bonus_rate_savings = db.Column(db.Float, default=0.01)

    # JSON list of {"min_balance": float, "bonus_rate": float}
    bonus_tiers = db.Column(db.Text, default='[{"min_balance":0,"bonus_rate":0.005},{"min_balance":10000,"bonus_rate":0.010},{"min_balance":50000,"bonus_rate":0.015},{"min_balance":100000,"bonus_rate":0.020}]')

    reward_points_per_100_kes = db.Column(db.Integer, default=1)
    streak_bonus_kes = db.Column(db.Numeric(12, 2), default=500)
    referral_bonus_kes = db.Column(db.Numeric(12, 2), default=200)

    tier_silver = db.Column(db.Integer, default=50)
    tier_gold = db.Column(db.Integer, default=200)
    tier_platinum = db.Column(db.Integer, default=500)

    min_monthly_deposit = db.Column(db.Numeric(12, 2), default=100)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get():
        s = SaccoSettings.query.first()
        if not s:
            s = SaccoSettings()
            db.session.add(s)
            db.session.commit()
        return s
