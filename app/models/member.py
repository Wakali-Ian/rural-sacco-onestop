from datetime import datetime
from app.models import db


class Member(db.Model):
    __tablename__ = "members"
    id = db.Column(db.Integer, primary_key=True)
    member_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    national_id = db.Column(db.String(20), unique=True)
    join_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default="active")
    savings_balance = db.Column(db.Numeric(12, 2), default=0)
    shares = db.Column(db.Integer, default=0)
    trust_score = db.Column(db.Float, default=50.0)
    default_rank = db.Column(db.String(1), default="C")
    language_preference = db.Column(db.String(5), default="sw")
    consent_given = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
