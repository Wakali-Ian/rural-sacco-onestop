from datetime import datetime
from app.models import db


class RewardAccount(db.Model):
    __tablename__ = "reward_accounts"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"),
                          unique=True, nullable=False, index=True)
    points = db.Column(db.Integer, default=0)
    tier = db.Column(db.String(20), default="bronze")
    streak_months = db.Column(db.Integer, default=0)
    last_deposit_month = db.Column(db.String(7))
    total_bonus_earned = db.Column(db.Numeric(12, 2), default=0)
    last_bonus_year = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)


class RewardTransaction(db.Model):
    __tablename__ = "reward_transactions"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"),
                          nullable=False, index=True)
    type = db.Column(db.String(30), nullable=False)
    points_delta = db.Column(db.Integer, default=0)
    kes_delta = db.Column(db.Numeric(12, 2), default=0)
    reason = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
