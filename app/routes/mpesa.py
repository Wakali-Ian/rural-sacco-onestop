"""M-Pesa callback webhook. Receives C2B confirmations from Safaricom."""
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.models import db
from app.models.mpesa import MpesaTransaction

mpesa_bp = Blueprint("mpesa", __name__, url_prefix="/mpesa")


@mpesa_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "endpoint": "mpesa"})


@mpesa_bp.route("/callback", methods=["POST"])
def c2b_callback():
    payload = request.get_json(silent=True) or {}
    body = payload.get("Body", payload)
    if "stkCallback" in body:
        body = body["stkCallback"]

    trans_id = body.get("TransID") or body.get("transactionId")
    if not trans_id:
        return jsonify({"ResultCode": 1, "ResultDesc": "Missing TransID"}), 400

    if MpesaTransaction.query.filter_by(trans_id=trans_id).first():
        return jsonify({"ResultCode": 0, "ResultDesc": "Duplicate, ignored"})

    trans = MpesaTransaction(
        trans_id=trans_id,
        trans_time=datetime.utcnow(),
        amount=body.get("TransAmount") or body.get("amount") or 0,
        msisdn=body.get("MSISDN") or body.get("phone") or "",
        first_name=body.get("FirstName", ""),
        account_ref=(body.get("BillRefNumber")
                     or body.get("account_ref") or ""),
        raw_json=str(payload),
        status="unmatched",
    )
    db.session.add(trans)
    db.session.commit()
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})
