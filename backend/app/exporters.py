"""CSV and PDF export (PDF via reportlab, generated locally)."""
import csv
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

TEAL, AQUA, CHARCOAL, BORDER = (colors.HexColor(c) for c in ("#A8D1D1", "#DFEBEB", "#263238", "#D4E1E1"))
TITLE = "Air-Gapped Predictive Copilot for Secure MPLS Operations"


def _fmt(value):
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def to_csv(columns, rows) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_fmt(row[c]) for c in columns])
    return buffer.getvalue().encode("utf-8")


def to_pdf(report_title: str, columns, rows, filters: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=28,
                            bottomMargin=24, title=report_title)
    styles = getSampleStyleSheet()
    small = styles["BodyText"].clone("small", fontSize=6.5, leading=8, textColor=CHARCOAL)
    head = styles["BodyText"].clone("head", fontSize=7, leading=8, textColor=CHARCOAL, fontName="Helvetica-Bold")
    active = ", ".join(f"{k}={v}" for k, v in filters.items() if v) or "none"
    story = [Paragraph(TITLE, styles["Title"]), Paragraph(report_title, styles["Heading2"]),
             Paragraph(f"Generated {datetime.now():%Y-%m-%d %H:%M} | Filters: {active} | Rows: {len(rows)}",
                       styles["BodyText"]), Spacer(1, 8)]
    data = [[Paragraph(c, head) for c in columns]] + [[Paragraph(_fmt(r[c]), small) for c in columns] for r in rows[:500]]
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AQUA]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()
