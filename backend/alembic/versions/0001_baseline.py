"""Baseline schema: all 13 tables from ORM metadata, plus views, stored procedures and triggers.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-19
"""
from alembic import op

from app.config import settings
from app.database import Base
from app.sql_loader import apply_sql_file
import app.models  # noqa: F401

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

SQL_DIR = settings.database_dir


def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind)
    for name in ("views.sql", "procedures.sql", "triggers.sql"):
        apply_sql_file(bind, SQL_DIR / name)


def downgrade():
    bind = op.get_bind()
    for trig in ("trg_telemetry_threshold_alert", "trg_incident_before_update", "trg_incident_status_audit",
                 "trg_audit_logs_no_update", "trg_audit_logs_no_delete"):
        bind.exec_driver_sql(f"DROP TRIGGER IF EXISTS {trig}")
    for proc in ("sp_open_incident_from_alert", "sp_device_risk_summary"):
        bind.exec_driver_sql(f"DROP PROCEDURE IF EXISTS {proc}")
    bind.exec_driver_sql("DROP VIEW IF EXISTS v_device_health, v_prediction_report")
    Base.metadata.drop_all(bind)
