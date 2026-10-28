from datetime import datetime
from app.models import db


class Loan(db.Model):
    __tablename__ = "loans"
    id = db.Column(db.Integer, primary_key=True)
    loan_number = db.Column(db.String(30), unique=True, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False, index=True)
    principal = db.Column(db.Numeric(12, 2), nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    interest_method = db.Column(db.String(20), default="flat")
    term_months = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.String(200))
    status = db.Column(db.String(20), default="pending")
    disbursement_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    outstanding_balance = db.Column(db.Numeric(12, 2), default=0)
    approved_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LoanRepayment(db.Model):
    __tablename__ = "loan_repayments"
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loans.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    principal_portion = db.Column(db.Numeric(12, 2), default=0)
    interest_portion = db.Column(db.Numeric(12, 2), default=0)
    penalty_portion = db.Column(db.Numeric(12, 2), default=0)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    mpesa_ref = db.Column(db.String(50))
    status = db.Column(db.String(20), default="completed")
