from flask import Blueprint, request
from app.services.ussd_service import handle_ussd

ussd_bp = Blueprint("ussd", __name__, url_prefix="/ussd")


@ussd_bp.route("/", methods=["POST"])
def ussd_callback():
    phone = request.form.get("phoneNumber", "")
    text = request.form.get("text", "")
    response = handle_ussd(phone, text)
    return response, 200, {"Content-Type": "text/plain; charset=utf-8"}
