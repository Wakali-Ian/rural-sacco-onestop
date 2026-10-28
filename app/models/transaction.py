from datetime import datetime
from app.models import db


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False, index=True)
    type = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2))
    reference = db.Column(db.String(50), unique=True, index=True)
    mpesa_ref = db.Column(db.String(50), index=True)
    status = db.Column(db.String(20), default="completed")
    channel = db.Column(db.String(20), default="manual")
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
