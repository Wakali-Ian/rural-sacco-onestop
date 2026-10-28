from datetime import datetime
from app.models import db


class Penalty(db.Model):
    __tablename__ = "penalties"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False, index=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loans.id"))
    type = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
