from datetime import datetime
from app.models import db


class EtimsConfig(db.Model):
    __tablename__ = "etims_config"
    id = db.Column(db.Integer, primary_key=True)
    kra_pin = db.Column(db.String(11), unique=True, nullable=False)
    branch_id = db.Column(db.String(2), default="00")
    device_serial = db.Column(db.String(50))
    cmc_key = db.Column(db.String(255))
    base_url = db.Column(db.String(200),
                         default="https://etims-api-sbx.kra.go.ke/etims-api")
    is_active = db.Column(db.Boolean, default=True)
    last_initialized = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def get_active():
        return EtimsConfig.query.filter_by(is_active=True).first()


class EtimsReceipt(db.Model):
    __tablename__ = "etims_receipts"
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer,
                               db.ForeignKey("transactions.id"),
                               nullable=False, index=True)
    invoice_no = db.Column(db.String(50), unique=True, index=True)
    receipt_signature = db.Column(db.Text)
    qr_url = db.Column(db.Text)
    control_unit_invoice_no = db.Column(db.String(50))
    raw_response = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
