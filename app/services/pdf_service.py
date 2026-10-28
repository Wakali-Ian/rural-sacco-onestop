"""Generate the AGM pack PDF: exec summary, ranks, top savers, aging, risks."""
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, PageBreak)
from app.models import db
from app.models.member import Member
from app.models.loan import Loan
from app.models.risk import RiskEvent


def _money(x):
    return f"KES {float(x or 0):,.0f}"


def generate_agm_report():
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title="SACCO AGM Report",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=20, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14,
                        spaceBefore=14, spaceAfter=6)
    body = styles["Normal"]

    story = [
        Paragraph("Rural SACCO OneStop Solutions", h1),
        Paragraph(f"AGM Report &mdash; {datetime.utcnow().strftime('%d %B %Y')}", body),
        Spacer(1, 0.5 * cm),
    ]

    total_members = Member.query.filter_by(status="active").count()
    total_savings = float(db.session.query(
        db.func.coalesce(db.func.sum(Member.savings_balance), 0)
    ).scalar() or 0)
    total_loans = float(db.session.query(
        db.func.coalesce(db.func.sum(Loan.outstanding_balance), 0)
    ).filter(Loan.status.in_(["active", "disbursed", "overdue"])).scalar() or 0)
    open_risks = RiskEvent.query.filter_by(status="open").count()
    ratio = (total_loans / total_savings * 100) if total_savings else 0.0

    summary_rows = [
        ["Active members", str(total_members)],
        ["Total savings", _money(total_savings)],
        ["Loan book (outstanding)", _money(total_loans)],
        ["Loan/savings ratio", f"{ratio:.1f}%"],
        ["Open risk events", str(open_risks)],
    ]
    story.append(Paragraph("Executive Summary", h2))
    t = Table(summary_rows, colWidths=[9 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
    ]))
    story.append(t)

    story.append(Paragraph("Default Rank Distribution", h2))
    dist = {}
    for m in Member.query.filter_by(status="active").all():
        dist[m.default_rank] = dist.get(m.default_rank, 0) + 1
    rank_rows = [["Rank", "Members", "Share"]]
    for rank in ["A", "B", "C", "D", "E"]:
        n = dist.get(rank, 0)
        pct = (n / total_members * 100) if total_members else 0
        rank_rows.append([rank, str(n), f"{pct:.1f}%"])
    t = Table(rank_rows, colWidths=[3 * cm, 3 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
    ]))
    story.append(t)

    story.append(Paragraph("Top 10 Savers", h2))
    top = Member.query.order_by(Member.savings_balance.desc()).limit(10).all()
    rows = [["Member No.", "Name", "Rank", "Savings"]]
    for m in top:
        rows.append([m.member_number, m.full_name, m.default_rank,
                     _money(m.savings_balance)])
    t = Table(rows, colWidths=[3.5 * cm, 6 * cm, 2 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
    ]))
    story.append(t)

    story.append(PageBreak())

    story.append(Paragraph("Overdue Loans &mdash; Aging Report", h2))
    today = datetime.utcnow().date()
    overdue = (Loan.query
               .filter(Loan.status.in_(["active", "disbursed", "overdue"]),
                       Loan.due_date.isnot(None),
                       Loan.outstanding_balance > 0)
               .order_by(Loan.due_date.asc()).all())
    rows = [["Loan No.", "Outstanding", "Due Date", "Days Late"]]
    shown = 0
    for loan in overdue:
        days = (today - loan.due_date).days
        if days <= 0:
            continue
        rows.append([loan.loan_number,
                     _money(loan.outstanding_balance),
                     loan.due_date.strftime("%d/%m/%Y"), str(days)])
        shown += 1
        if shown >= 20:
            break
    if shown == 0:
        rows.append(["—", "No overdue loans.", "—", "—"])
    t = Table(rows, colWidths=[4 * cm, 4 * cm, 4 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
    ]))
    story.append(t)

    story.append(Paragraph("Open Risks", h2))
    risks = (RiskEvent.query.filter_by(status="open")
             .order_by(RiskEvent.created_at.desc()).limit(15).all())
    rows = [["Type", "Severity", "Description"]]
    for r in risks:
        desc = r.description[:70] + ("…" if len(r.description) > 70 else "")
        rows.append([r.risk_type, r.severity.upper(), Paragraph(desc, body)])
    if not risks:
        rows.append(["—", "—", "No open risks."])
    t = Table(rows, colWidths=[3 * cm, 2 * cm, 10 * cm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"<i>Generated by Rural SACCO OneStop Solutions on "
        f"{datetime.utcnow().strftime('%d %B %Y at %H:%M UTC')}. "
        f"Auto-generated and audit-ready.</i>",
        body))

    doc.build(story)
    buf.seek(0)
    return buf
