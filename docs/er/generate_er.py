"""Generates ER diagrams (Mermaid, PNG, SVG, PDF), relational schema and data dictionary directly from
the SQLAlchemy metadata, so the documentation always matches the implemented schema exactly.
Run from project root: python docs/er/generate_er.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))
for key, value in {"MYSQL_HOST": "x", "MYSQL_PORT": "3306", "MYSQL_USER": "x", "MYSQL_PASSWORD": "x",
                   "MYSQL_DATABASE": "x", "JWT_SECRET": "x", "JWT_EXPIRE_MINUTES": "60", "CORS_ORIGINS": "x"}.items():
    os.environ.setdefault(key, value)  # metadata only; no DB connection is opened

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from app.database import Base  # noqa: E402
import app.models  # noqa: E402,F401

OUT = Path(__file__).resolve().parent
DOCS = OUT.parent
TABLES = Base.metadata.sorted_tables
TEAL, AQUA, INK, BORDER = "#A8D1D1", "#DFEBEB", "#263238", "#9FBFBF"
LAYOUT = {  # grid positions (col, row) for readability
    "roles": (0, 0), "users": (1, 0), "revoked_tokens": (0, 1), "audit_logs": (2, 0),
    "sites": (0, 2), "devices": (1, 2), "telemetry": (2, 2), "predictions": (3, 2),
    "recommendations": (3, 3), "alerts": (2, 3), "incidents": (1, 3), "engineer_actions": (1, 4), "outcomes": (2, 4),
}


def col_type(c):
    return str(c.type.compile(dialect=__import__("sqlalchemy.dialects.mysql", fromlist=["dialect"]).dialect()))


def relationships():
    rels = []
    for t in TABLES:
        for fk in t.foreign_keys:
            child_col = fk.parent
            unique = bool(child_col.unique)
            rels.append((fk.column.table.name, t.name, child_col.name, child_col.nullable, bool(unique)))
    return rels


def mermaid():
    lines = ["erDiagram"]
    for t in TABLES:
        lines.append(f"    {t.name} {{")
        fks = {fk.parent.name for fk in t.foreign_keys}
        for c in t.columns:
            keys = ",".join(k for k, ok in (("PK", c.primary_key), ("FK", c.name in fks), ("UK", c.unique)) if ok)
            lines.append(f"        {col_type(c).split('(')[0].replace(' ', '_')} {c.name} {keys}".rstrip())
        lines.append("    }")
    for parent, child, col, nullable, unique in relationships():
        left = "|o" if nullable else "||"
        right = "o|" if unique else "o{"
        lines.append(f'    {parent} {left}--{right} {child} : "{col}"')
    return "\n".join(lines) + "\n"


def draw(detailed: bool, stem: str):
    box_w, row_h = (4.2, 0.26) if detailed else (2.6, 0.0)
    gap_x, gap_y = 1.6, 1.2
    heights = {t.name: (0.5 + row_h * len(t.columns)) if detailed else 0.8 for t in TABLES}
    row_heights = {}
    for name, (cx, ry) in LAYOUT.items():
        row_heights[ry] = max(row_heights.get(ry, 0), heights[name])
    row_y, y = {}, 0
    for r in sorted(row_heights):
        row_y[r] = y
        y -= row_heights[r] + gap_y
    pos = {n: (cx * (box_w + gap_x), row_y[ry]) for n, (cx, ry) in LAYOUT.items()}
    width, height = 4 * (box_w + gap_x), -y
    fig, ax = plt.subplots(figsize=(width * 0.95, height * 0.95))
    ax.set_xlim(-0.5, width)
    ax.set_ylim(y, 1.2)
    ax.axis("off")
    for parent, child, col, nullable, unique in relationships():
        (px, py), (cx, cy) = pos[parent], pos[child]
        p_mid = (px + box_w / 2, py - heights[parent] / 2)
        c_mid = (cx + box_w / 2, cy - heights[child] / 2)
        ax.annotate("", xy=c_mid, xytext=p_mid, arrowprops=dict(arrowstyle="-|>", color="#667477", lw=1,
                                                                 connectionstyle="arc3,rad=0.12", shrinkA=18, shrinkB=18))
        label = f"{col}\n1 : {'1' if unique else 'N'}{' (opt)' if nullable else ''}"
        ax.text((p_mid[0] + c_mid[0]) / 2, (p_mid[1] + c_mid[1]) / 2, label, fontsize=6.5 if detailed else 8,
                color="#2F5F5F", ha="center", va="center", bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.5))
    for t in TABLES:
        x0, y0 = pos[t.name]
        h = heights[t.name]
        ax.add_patch(FancyBboxPatch((x0, y0 - h), box_w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc="white", ec=BORDER, lw=1.2))
        ax.add_patch(FancyBboxPatch((x0, y0 - 0.45), box_w, 0.45, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=TEAL, ec=BORDER, lw=1.2))
        ax.text(x0 + box_w / 2, y0 - 0.23, t.name, ha="center", va="center", fontsize=11 if detailed else 12,
                fontweight="bold", color=INK)
        if detailed:
            fks = {fk.parent.name for fk in t.foreign_keys}
            for i, c in enumerate(t.columns):
                cy = y0 - 0.6 - i * row_h
                if i % 2:
                    ax.add_patch(plt.Rectangle((x0 + 0.02, cy - row_h / 2), box_w - 0.04, row_h, fc=AQUA, ec="none"))
                tag = " ".join(k for k, ok in (("PK", c.primary_key), ("FK", c.name in fks), ("UQ", c.unique),
                                               ("NN", not c.nullable and not c.primary_key)) if ok)
                ax.text(x0 + 0.1, cy, c.name, fontsize=7.5, va="center", color=INK,
                        fontweight="bold" if c.primary_key else "normal")
                ax.text(x0 + box_w * 0.52, cy, col_type(c).lower()[:18], fontsize=7, va="center", color="#667477")
                ax.text(x0 + box_w - 0.08, cy, tag, fontsize=6.5, va="center", ha="right", color="#2F5F5F")
    title = "Detailed ER diagram" if detailed else "ER diagram (presentation)"
    ax.text(0, 0.8, f"Air-Gapped Predictive Copilot for Secure MPLS Operations - {title}", fontsize=14,
            fontweight="bold", color=INK)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=170 if ext == "png" else None, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def relational_schema():
    lines = ["# Relational Schema (generated from ORM metadata)", "",
             "Notation: **PK** underlined-equivalent in bold, *FK* in italics with reference.", ""]
    for t in TABLES:
        fks = {fk.parent.name: f"{fk.column.table.name}.{fk.column.name}" for fk in t.foreign_keys}
        cols = []
        for c in t.columns:
            if c.primary_key:
                cols.append(f"**{c.name}**")
            elif c.name in fks:
                cols.append(f"*{c.name}* → {fks[c.name]}")
            else:
                cols.append(c.name)
        lines.append(f"- **{t.name.upper()}**({', '.join(cols)})")
    return "\n".join(lines) + "\n"


def data_dictionary():
    out = ["# Data Dictionary (generated from ORM metadata)", ""]
    for t in TABLES:
        fks = {fk.parent.name: fk for fk in t.foreign_keys}
        checks = [str(c.sqltext) for c in t.constraints if c.__class__.__name__ == "CheckConstraint"]
        out += [f"## {t.name}", "", "| Column | Type | Null | Key | Default | References |", "|---|---|---|---|---|---|"]
        for c in t.columns:
            key = "PK" if c.primary_key else ("FK" if c.name in fks else ("UQ" if c.unique else ""))
            default = c.server_default.arg if c.server_default is not None else ""
            ref = ""
            if c.name in fks:
                fk = fks[c.name]
                ref = f"{fk.column.table.name}.{fk.column.name} ON DELETE {fk.ondelete or 'RESTRICT'}"
            out.append(f"| {c.name} | {col_type(c)} | {'YES' if c.nullable else 'NO'} | {key} | {default} | {ref} |")
        if checks:
            out += ["", "CHECK constraints: " + "; ".join(f"`{c}`" for c in checks)]
        idx = [f"`{i.name}` ({', '.join(c.name for c in i.columns)})" for i in t.indexes]
        if idx:
            out += ["", "Indexes: " + ", ".join(idx)]
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    (OUT / "er_diagram.mmd").write_text(mermaid())
    draw(True, "er_diagram_detailed")
    draw(False, "er_diagram_presentation")
    (DOCS / "09_relational_schema.md").write_text(relational_schema())
    (DOCS / "10_data_dictionary.md").write_text(data_dictionary())
    print(f"{len(TABLES)} tables, {len(relationships())} relationships written to {OUT}")
