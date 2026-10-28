from datetime import datetime
from flask import Blueprint, send_file
from app.services.auth import login_required
from app.services.pdf_service import generate_agm_report

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/agm.pdf")
@login_required
def agm_pdf():
    buf = generate_agm_report()
    fname = f"sacco_agm_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=fname)
