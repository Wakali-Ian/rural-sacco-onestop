from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from app.models.member import Member
from app.models.transaction import Transaction
from app.models.mpesa import MpesaTransaction
from app.models.loan import Loan, LoanRepayment
from app.models.guarantor import Guarantor
from app.models.meeting import Meeting, MeetingAttendance
from app.models.penalty import Penalty
from app.models.risk import RiskEvent
from app.models.audit import AuditLog
from app.models.user import User
