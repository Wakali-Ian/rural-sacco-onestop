from datetime import datetime
from app.models import db


class Guarantor(db.Model):
    __tablename__ = "guarantors"
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loans.id"), nullable=False, index=True)
    guarantor_member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    amount_guaranteed = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
