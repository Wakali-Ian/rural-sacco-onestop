from datetime import datetime
from app.models import db


class RiskEvent(db.Model):
    __tablename__ = "risk_events"
    id = db.Column(db.Integer, primary_key=True)
    risk_type = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"))
    loan_id = db.Column(db.Integer, db.ForeignKey("loans.id"))
    mitigation = db.Column(db.Text)
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
