from flask import Blueprint, request, Response
from app.services.ivr_service import handle_voice_call

voice_bp = Blueprint("voice", __name__, url_prefix="/voice")


@voice_bp.route("/", methods=["POST"])
def voice_callback():
    phone = (request.form.get("callerNumber")
             or request.form.get("callerId") or "")
    result = handle_voice_call(phone)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="female">{result['text']}</Say>
</Response>"""
    return Response(xml, mimetype="application/xml")
