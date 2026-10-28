from datetime import datetime
from app.models import db


class MpesaTransaction(db.Model):
    __tablename__ = "mpesa_transactions"
    id = db.Column(db.Integer, primary_key=True)
    trans_id = db.Column(db.String(30), unique=True, index=True)
    trans_time = db.Column(db.DateTime)
    amount = db.Column(db.Numeric(12, 2))
    msisdn = db.Column(db.String(20), index=True)
    first_name = db.Column(db.String(50))
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    account_ref = db.Column(db.String(50), index=True)
    org_account_balance = db.Column(db.Numeric(12, 2))
    raw_json = db.Column(db.Text)
    matched_transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"))
    matched_at = db.Column(db.DateTime)
    match_method = db.Column(db.String(30))
    match_confidence = db.Column(db.Float)
    status = db.Column(db.String(20), default="unmatched")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
