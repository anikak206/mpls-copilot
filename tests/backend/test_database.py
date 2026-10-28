"""Schema, constraints, views, stored procedures, triggers and transactions (real MySQL)."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError

EXPECTED_TABLES = {"roles", "users", "revoked_tokens", "sites", "devices", "telemetry", "predictions",
                   "recommendations", "alerts", "incidents", "engineer_actions", "outcomes", "audit_logs"}


def scalar(db, sql, **params):
    return db.execute(text(sql), params).scalar()


def test_connection_and_tables(client, db):
    assert scalar(db, "SELECT 1") == 1
    tables = {r[0] for r in db.execute(text(
        "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE'"))}
    assert EXPECTED_TABLES <= tables
    assert scalar(db, "SELECT version_num FROM alembic_version") == "0001_baseline"


def test_foreign_keys_and_indexes(client, db):
    fks = scalar(db, "SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=DATABASE()")
    assert fks >= 20
    idx = {r[0] for r in db.execute(text(
        "SELECT DISTINCT INDEX_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE()"))}
    assert {"ix_telemetry_device_time", "ix_alerts_device_status", "ix_audit_created"} <= idx


def test_check_constraint_rejects_out_of_range(client, db):
    with pytest.raises((OperationalError, IntegrityError, DBAPIError)):
        db.execute(text("INSERT INTO telemetry (device_id, cpu_util, mem_util, latency_ms, jitter_ms, packet_loss_pct,"
                        " throughput_mbps, source) VALUES (1, 150, 50, 10, 1, 0, 100, 'manual')"))
    db.rollback()


def test_unique_and_fk_constraints(client, db):
    with pytest.raises(IntegrityError):
        db.execute(text("INSERT INTO devices (hostname, mgmt_ip, device_type, vendor, model, site_id) "
                        "SELECT hostname, '192.0.2.250', 'PE', 'x', 'y', site_id FROM devices LIMIT 1"))
    db.rollback()
    with pytest.raises(IntegrityError):
        db.execute(text("INSERT INTO devices (hostname, mgmt_ip, device_type, vendor, model, site_id) "
                        "VALUES ('fk-test', '192.0.2.251', 'PE', 'x', 'y', 99999)"))
    db.rollback()


def test_views_return_rows(client, db):
    assert scalar(db, "SELECT COUNT(*) FROM v_device_health") == 12
    assert scalar(db, "SELECT COUNT(*) FROM v_prediction_report") >= 36


def test_procedure_risk_summary(client, db):
    rows = db.execute(text("CALL sp_device_risk_summary(7)")).mappings().all()
    assert len(rows) == 12 and {"hostname", "avg_risk", "anomalies"} <= set(rows[0].keys())
    db.rollback()
    with pytest.raises(DBAPIError):
        db.execute(text("CALL sp_device_risk_summary(0)"))
    db.rollback()


def test_trigger_raises_alert_on_threshold_breach(client, db):
    db.execute(text("INSERT INTO telemetry (device_id, cpu_util, mem_util, latency_ms, jitter_ms, packet_loss_pct,"
                    " throughput_mbps, source) VALUES (1, 97, 50, 10, 1, 0, 100, 'manual')"))
    tid = scalar(db, "SELECT LAST_INSERT_ID()")
    db.commit()
    assert scalar(db, "SELECT severity FROM alerts WHERE telemetry_id=:t AND source='trigger'", t=tid) == "critical"
    db.execute(text("INSERT INTO telemetry (device_id, cpu_util, mem_util, latency_ms, jitter_ms, packet_loss_pct,"
                    " throughput_mbps, source) VALUES (1, 30, 50, 10, 1, 0, 100, 'manual')"))
    tid = scalar(db, "SELECT LAST_INSERT_ID()")
    db.commit()
    assert scalar(db, "SELECT COUNT(*) FROM alerts WHERE telemetry_id=:t", t=tid) == 0


def test_incident_triggers_audit_and_closed_at(client, db):
    iid = scalar(db, "SELECT MIN(incident_id) FROM incidents")
    before = scalar(db, "SELECT COUNT(*) FROM audit_logs WHERE action='incident_status_changed' AND entity_id=:i", i=str(iid))
    db.execute(text("SET @app_user_id = 1"))
    db.execute(text("UPDATE incidents SET status='closed' WHERE incident_id=:i"), {"i": iid})
    db.commit()
    assert scalar(db, "SELECT closed_at IS NOT NULL FROM incidents WHERE incident_id=:i", i=iid) == 1
    db.execute(text("UPDATE incidents SET description=CONCAT(description,' ') WHERE incident_id=:i"), {"i": iid})
    db.commit()
    after = scalar(db, "SELECT COUNT(*) FROM audit_logs WHERE action='incident_status_changed' AND entity_id=:i", i=str(iid))
    assert after == before + 1  # non-status update does not log (no duplicates)


def test_audit_logs_are_append_only(client, db):
    with pytest.raises(DBAPIError):
        db.execute(text("UPDATE audit_logs SET action='tampered' LIMIT 1"))
    db.rollback()
    with pytest.raises(DBAPIError):
        db.execute(text("DELETE FROM audit_logs LIMIT 1"))
    db.rollback()


def test_procedure_escalation_commit_and_rollback(client, admin):
    alerts = client.get("/api/alerts?status=open&page_size=50", headers=admin).json()["items"]
    alert = next(a for a in alerts if a["incident_id"] is None)
    r = client.post(f"/api/alerts/{alert['alert_id']}/escalate", headers=admin)
    assert r.status_code == 201, r.text
    incidents_total = client.get("/api/incidents", headers=admin).json()["total"]
    again = client.post(f"/api/alerts/{alert['alert_id']}/escalate", headers=admin)
    assert again.status_code == 400 and "already linked" in again.json()["detail"]
    assert client.get("/api/incidents", headers=admin).json()["total"] == incidents_total  # rolled back


def test_transaction_demo_rollback_and_commit(client, admin):
    r = client.post("/api/db-lab/transaction-demo", json={"simulate_failure": True}, headers=admin).json()
    assert r["outcome"] == "rolled_back" and r["counts_before"] == r["counts_after"]
    r = client.post("/api/db-lab/transaction-demo", json={"simulate_failure": False}, headers=admin).json()
    assert r["outcome"] == "committed"
    assert r["counts_after"]["incidents"] == r["counts_before"]["incidents"] + 1
    assert r["counts_after"]["alerts"] == r["counts_before"]["alerts"] + 1


def test_join_and_aggregate_queries(client, auditor):
    data = client.get("/api/db-lab/queries", headers=auditor).json()
    categories = {q["category"] for q in data["queries"]}
    assert {"JOIN", "AGGREGATE", "VIEW", "PROCEDURE"} <= categories
    assert all(q["rows"] is not None for q in data["queries"])
    kinds = {o["kind"] for o in data["database_objects"]}
    assert kinds == {"TRIGGER", "PROCEDURE", "VIEW"}
