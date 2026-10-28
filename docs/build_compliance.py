"""Builds docs/20_compliance_matrix.md and docs/20_compliance_matrix.pdf from the evidence table below.
Run from project root: python docs/build_compliance.py
"""
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DOCS = Path(__file__).resolve().parent
T = "pytest"
# (requirement, implementation, location, test performed, result, status, missing work)
SECTIONS = [
    ("1. Problem Statement & Project Planning", 2, 1.5, [
        ("Project title, problem statement, objectives, scope", "Written proposal", "docs/01_project_proposal.md", "Inspected", "Present", "PASS", "—"),
        ("Team members & responsibilities", "Editable template only", "docs/01_project_proposal.md", "Inspected", "Placeholders", "PARTIAL", "Fill real names/IDs and tasks"),
        ("Technology stack & deliverables", "Table incl. documented CRA deviation", "docs/01_project_proposal.md", "Inspected", "Present", "PASS", "—"),
        ("Gantt chart", "Mermaid gantt + week table (template dates)", "docs/01_project_proposal.md", "Inspected", "Present", "PASS", "Adjust dates to semester"),
    ]),
    ("2. Database Design", 6, 6, [
        ("ER diagram", "Generated from ORM metadata: detailed + presentation (PNG/SVG/PDF) + Mermaid", "docs/er/", "Generator run; 13 tables / 24 FKs", "Matches schema", "PASS", "—"),
        ("Min. 4 primary entities", "13 tables", "backend/app/models.py, database/schema.sql", f"{T} test_connection_and_tables", "Passed", "PASS", "—"),
        ("Min. 3 relationships", "24 foreign keys (1:N, 1:1)", "docs/07_08_er_diagrams.md", f"{T} test_foreign_keys_and_indexes", "Passed", "PASS", "—"),
        ("Relational schema", "Generated from metadata", "docs/09_relational_schema.md", "Inspected", "Present", "PASS", "—"),
        ("Keys & constraints (PK, FK, UNIQUE, CHECK, NOT NULL, DEFAULT)", "23 CHECK constraints, UNIQUE keys, FK actions", "database/schema.sql", f"{T} constraint tests", "Passed", "PASS", "—"),
        ("Normalization 3NF", "Analysis with justified exceptions", "docs/11_normalization_3nf.md", "Inspected", "Present", "PASS", "—"),
        ("Data dictionary (recommended)", "Generated per table", "docs/10_data_dictionary.md", "Inspected", "Present", "PASS", "—"),
    ]),
    ("3. Database Implementation", 8, 8, [
        ("Database creation & table design", "Alembic 0001_baseline + schema.sql", "backend/alembic, database/schema.sql", f"{T} schema tests", "Passed", "PASS", "—"),
        ("CRUD", "ORM create/read/update/delete via API", "backend/app/routers/devices.py etc.", f"{T} test_device_crud_and_validation", "Passed", "PASS", "—"),
        ("JOIN queries", "Reports, Database Lab, ORM joins", "app/routers/dblab.py, app/reports.py", f"{T} test_join_and_aggregate_queries", "Passed", "PASS", "—"),
        ("Views", "v_device_health, v_prediction_report", "database/views.sql", f"{T} test_views_return_rows", "Passed", "PASS", "—"),
        ("Aggregate queries", "Dashboard GROUP BY, DB Lab, procedure", "app/routers/reports.py", f"{T} + E2E dashboard", "Passed", "PASS", "—"),
        ("Transactions (commit & rollback)", "Prediction workflow, actions, transaction demo, procedure", "app/routers/predictions.py, dblab.py", f"{T} test_transaction_demo_rollback_and_commit", "Passed", "PASS", "—"),
        ("Stored procedure / trigger", "2 procedures, 5 triggers", "database/procedures.sql, triggers.sql", f"{T} procedure + trigger tests", "Passed", "PASS", "—"),
        ("ORM integration", "SQLAlchemy 2 for all app access", "backend/app/", f"{T} API tests persist to MySQL", "Passed", "PASS", "—"),
    ]),
    ("4. Application Development", 4, 4, [
        ("Framework-based application", "FastAPI + React", "backend/, frontend/", "Build + E2E", "Passed", "PASS", "—"),
        ("Dashboard", "Stats, charts, recent activity", "frontend/src/pages/Dashboard.js", "E2E", "Passed", "PASS", "—"),
        ("Search / filtering / pagination", "All list pages", "frontend/src/pages/*", f"{T} test_pagination + E2E", "Passed", "PASS", "—"),
        ("Validation", "Pydantic + frontend validators + DB CHECK", "app/schemas.py, src/lib/validation.js", f"{T} + Jest 4 tests", "Passed", "PASS", "—"),
        ("Exception handling", "Mapped 401/403/404/409/422/429/500", "backend/server.py", f"{T}", "Passed", "PASS", "—"),
        ("Responsive UI", "CSS breakpoints 1100/860 px", "frontend/src/App.css", "E2E 390 px + screenshots", "Passed after fix", "PASS", "—"),
    ]),
    ("5. Authentication, Authorization & Database Security", 5, 5, [
        ("JWT authentication", "Login, me, logout with revocation, expiry", "app/routers/auth.py, app/security.py", f"{T} auth tests + E2E", "Passed", "PASS", "—"),
        ("RBAC using single Users table", "users + roles; require_roles on every endpoint; engineer scoping", "app/security.py", f"{T} test_rbac_forbidden_actions", "Passed", "PASS", "—"),
        ("ORM-based authorization", "scope_to_assigned() filters SQLAlchemy queries", "app/security.py", f"{T} test_engineer_sees_only_assigned_devices", "Passed", "PASS", "—"),
        ("Password hashing", "bcrypt cost 12", "app/security.py", f"{T} test_password_is_bcrypt_hashed", "Passed", "PASS", "—"),
        ("SQL injection prevention", "ORM + bound parameters, whitelisted filters", "app/reports.py", "Code inspection", "No string-built user SQL", "PASS", "—"),
        ("Secrets management", ".env + .env.example + .gitignore", "backend/.env (excluded), .env.example", "Inspected ZIP", "No secrets packaged", "PASS", "—"),
    ]),
    ("6. Professional Development Practices", 5, 1.5, [
        ("GitHub: progressive commits & branching", "Documented main/dev workflow", "README.md §10", "—", "No repository exists", "NOT VERIFIABLE", "Create repo; commit progressively; create dev branch"),
        (".gitignore", "Excludes .env, venvs, node_modules, DB data", ".gitignore", "Inspected", "Present", "PASS", "—"),
        ("Database backup & restore", "scripts/backup.sh, guide", "docs/17_backup_recovery.md", "Dump + restore into test DB", "Passed", "PASS", "—"),
        ("Docker", "docker-compose.yml, 2 Dockerfiles", "docker-compose.yml", "Not executed (no Docker in env)", "Unverified", "PARTIAL", "Run docker compose up and record evidence"),
        ("Docker Hub", "Instructions only", "README.md §11", "—", "Not done", "MISSING", "Push images to Docker Hub"),
        ("Cloud deployment (live URL)", "Guide only", "README.md §11", "—", "Not deployed", "MISSING", "Deploy with a MySQL-capable host and record URL"),
    ]),
]
BONUS = [
    ("CI/CD pipeline (GitHub Actions)", "Workflow written (pytest on MySQL + frontend build)", ".github/workflows/ci.yml", "PARTIAL — not run", "+0 until it runs green on GitHub"),
    ("Custom domain", "None", "—", "MISSING", "+0"),
    ("Additional best practice: automated testing + append-only audit logging", "37 pytest + 4 Jest + E2E; trigger-enforced audit", "tests/, database/triggers.sql", "PASS", "+1"),
]


def build():
    total_max = sum(s[1] for s in SECTIONS)
    total = sum(s[2] for s in SECTIONS)
    md = [f"# 20. Faculty Rubric Compliance Matrix", "", f"Generated {date.today().isoformat()}. Marks are an evidence-based **estimate**; "
          "items only described in documentation are not awarded.", "",
          "| Category | Max | Estimated |", "|---|---|---|"]
    md += [f"| {s[0]} | {s[1]} | {s[2]} |" for s in SECTIONS] + [f"| **Total** | **{total_max}** | **{total}** |", ""]
    for title, mx, est, rows in SECTIONS:
        md += [f"## {title} — {est}/{mx}", "", "| Requirement | Implementation | Location | Test | Result | Status | Missing work |",
               "|---|---|---|---|---|---|---|"]
        md += ["| " + " | ".join(r) + " |" for r in rows] + [""]
    md += ["## Bonus opportunities (assessed separately)", "", "| Bonus | Implementation | Location | Status | Estimate |", "|---|---|---|---|---|"]
    md += ["| " + " | ".join(b) + " |" for b in BONUS]
    md += ["", "Estimated bonus: **+1** (verified automated testing and audit logging).",
           "", "Marks impact: the main deductions are in Professional Practices (no verified GitHub history, Docker run, Docker Hub or cloud deployment) and Planning (team placeholders)."]
    (DOCS / "20_compliance_matrix.md").write_text("\n".join(md) + "\n")

    styles = getSampleStyleSheet()
    cell = styles["BodyText"].clone("cell", fontSize=7, leading=8.5)
    head = cell.clone("head", fontName="Helvetica-Bold")
    status_bg = {"PASS": "#E3F2EA", "PARTIAL": "#FFF3D6", "MISSING": "#FBE0E3", "NOT VERIFIABLE": "#E6EEF2"}
    doc = SimpleDocTemplate(str(DOCS / "20_compliance_matrix.pdf"), pagesize=landscape(A4), leftMargin=22, rightMargin=22,
                            topMargin=24, bottomMargin=22, title="Faculty Compliance Matrix")
    story = [Paragraph("Air-Gapped Predictive Copilot for Secure MPLS Operations", styles["Title"]),
             Paragraph(f"Faculty rubric compliance matrix — generated {date.today().isoformat()}", styles["Heading2"]),
             Paragraph("Evidence-based estimate. Features that only appear in documentation are not awarded marks.", styles["BodyText"]),
             Spacer(1, 8)]
    summary = [["Category", "Max", "Estimated"]] + [[s[0], s[1], s[2]] for s in SECTIONS] + [["Total", total_max, total]]
    t = Table(summary, colWidths=[420, 60, 70])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#A8D1D1")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D4E1E1")),
                           ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#DFEBEB"))]))
    story += [t, Spacer(1, 6), Paragraph("Estimated bonus: +1 (automated testing + audit logging verified). CI/CD written but not run; no custom domain.", styles["BodyText"]), PageBreak()]
    widths = [120, 150, 125, 110, 70, 62, 120]
    for title, mx, est, rows in SECTIONS:
        data = [[Paragraph(h, head) for h in ("Requirement", "Implementation", "Location", "Test", "Result", "Status", "Missing work")]]
        data += [[Paragraph(c, cell) for c in r] for r in rows]
        tbl = Table(data, colWidths=widths, repeatRows=1)
        style = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#A8D1D1")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D4E1E1")), ("VALIGN", (0, 0), (-1, -1), "TOP")]
        style += [("BACKGROUND", (5, i), (5, i), colors.HexColor(status_bg[r[5]])) for i, r in enumerate(rows, start=1)]
        tbl.setStyle(TableStyle(style))
        story += [Paragraph(f"{title} — {est}/{mx}", styles["Heading3"]), tbl, Spacer(1, 8)]
    bdata = [[Paragraph(h, head) for h in ("Bonus", "Implementation", "Location", "Status", "Estimate")]] + [[Paragraph(c, cell) for c in b] for b in BONUS]
    bt = Table(bdata, colWidths=[170, 220, 150, 120, 100], repeatRows=1)
    bt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#A8D1D1")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D4E1E1"))]))
    story += [Paragraph("Bonus opportunities", styles["Heading3"]), bt]
    doc.build(story)
    print(f"Compliance matrix written: {total}/{total_max}")


if __name__ == "__main__":
    build()
