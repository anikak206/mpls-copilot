"""Database Lab: live demonstrations of JOIN, aggregate, view, procedure and transaction behaviour."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, AuditLog, Device, Incident, User
from app.security import ADMIN, ALL_ROLES, require_roles

router = APIRouter(prefix="/api/db-lab", tags=["Database Lab"])

DEMO_QUERIES = [
    ("JOIN", "Open alerts with device, site and linked incident",
     "SELECT a.alert_id, d.hostname, s.name AS site, a.severity, a.status, i.title AS incident\n"
     "FROM alerts a\nJOIN devices d ON d.device_id = a.device_id\nJOIN sites s ON s.site_id = d.site_id\n"
     "LEFT JOIN incidents i ON i.incident_id = a.incident_id\nWHERE a.status <> 'resolved'\n"
     "ORDER BY a.created_at DESC LIMIT 10"),
    ("JOIN", "Predictions with telemetry, device and recommendation",
     "SELECT p.prediction_id, d.hostname, t.recorded_at, p.label, p.risk_score, r.title AS recommendation\n"
     "FROM predictions p\nJOIN telemetry t ON t.telemetry_id = p.telemetry_id\n"
     "JOIN devices d ON d.device_id = t.device_id\nLEFT JOIN recommendations r ON r.prediction_id = p.prediction_id\n"
     "ORDER BY p.risk_score DESC LIMIT 10"),
    ("JOIN", "Engineer actions with outcome and engineer",
     "SELECT ea.action_id, u.full_name AS engineer, d.hostname, ea.action_type, o.result\n"
     "FROM engineer_actions ea\nJOIN users u ON u.user_id = ea.engineer_id\nJOIN devices d ON d.device_id = ea.device_id\n"
     "LEFT JOIN outcomes o ON o.action_id = ea.action_id\nORDER BY ea.performed_at DESC LIMIT 10"),
    ("AGGREGATE", "Devices per site and status",
     "SELECT s.name AS site, d.status, COUNT(*) AS devices\nFROM devices d JOIN sites s ON s.site_id = d.site_id\n"
     "GROUP BY s.name, d.status ORDER BY s.name"),
    ("AGGREGATE", "Average telemetry per device (last 24h)",
     "SELECT d.hostname, COUNT(*) AS samples, ROUND(AVG(t.cpu_util),2) AS avg_cpu,\n"
     "       ROUND(AVG(t.latency_ms),2) AS avg_latency, ROUND(MAX(t.packet_loss_pct),3) AS max_loss\n"
     "FROM telemetry t JOIN devices d ON d.device_id = t.device_id\n"
     "WHERE t.recorded_at >= NOW() - INTERVAL 1 DAY\nGROUP BY d.hostname HAVING COUNT(*) > 0 ORDER BY avg_latency DESC"),
    ("AGGREGATE", "Risk distribution and alerts per day",
     "SELECT DATE(p.created_at) AS day, p.risk_level, COUNT(*) AS predictions, ROUND(AVG(p.risk_score),2) AS avg_risk\n"
     "FROM predictions p GROUP BY DATE(p.created_at), p.risk_level ORDER BY day DESC, avg_risk DESC"),
    ("VIEW", "v_device_health (top 10 by risk)",
     "SELECT hostname, site_name, status, open_alerts, avg_cpu_24h, avg_latency_24h, latest_risk_score, latest_risk_level\n"
     "FROM v_device_health ORDER BY latest_risk_score DESC LIMIT 10"),
    ("VIEW", "v_prediction_report grouped by label",
     "SELECT label, COUNT(*) AS predictions, ROUND(AVG(risk_score),2) AS avg_risk\nFROM v_prediction_report GROUP BY label"),
    ("PROCEDURE", "CALL sp_device_risk_summary(7)", "CALL sp_device_risk_summary(7)"),
]


@router.get("/queries")
def run_demo_queries(db: Session = Depends(get_db), _=Depends(require_roles(*ALL_ROLES))):
    results = []
    for category, title, sql in DEMO_QUERIES:
        result = db.execute(text(sql))
        columns = list(result.keys())
        results.append({"category": category, "title": title, "sql": sql, "columns": columns,
                        "rows": [dict(zip(columns, r)) for r in result.fetchall()]})
    objects = db.execute(text(
        "SELECT 'TRIGGER' AS kind, TRIGGER_NAME AS name, CONCAT(ACTION_TIMING,' ',EVENT_MANIPULATION,' ON ',"
        "EVENT_OBJECT_TABLE) AS detail FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE() "
        "UNION ALL SELECT 'PROCEDURE', ROUTINE_NAME, ROUTINE_TYPE FROM information_schema.ROUTINES "
        "WHERE ROUTINE_SCHEMA = DATABASE() UNION ALL SELECT 'VIEW', TABLE_NAME, 'VIEW' FROM "
        "information_schema.VIEWS WHERE TABLE_SCHEMA = DATABASE()")).mappings().all()
    return {"queries": results, "database_objects": [dict(o) for o in objects]}


class TransactionDemo(BaseModel):
    simulate_failure: bool = False


def _counts(db: Session):
    return {"incidents": db.scalar(select(func.count()).select_from(Incident)),
            "alerts": db.scalar(select(func.count()).select_from(Alert)),
            "audit_logs": db.scalar(select(func.count()).select_from(AuditLog))}


@router.post("/transaction-demo")
def transaction_demo(body: TransactionDemo, request: Request, db: Session = Depends(get_db),
                     user: User = Depends(require_roles(ADMIN))):
    """Inserts incident + alert + audit row in ONE transaction; optional failure before COMMIT -> ROLLBACK."""
    device = db.scalars(select(Device).order_by(Device.device_id).limit(1)).first()
    if device is None:
        raise HTTPException(400, "No device available for the demo")
    before = _counts(db)
    db.commit()
    steps = []
    try:
        incident = Incident(device_id=device.device_id, title="[Transaction demo] Maintenance check",
                            description="Created by the Database Lab transaction demonstration.",
                            severity="info", opened_by=user.user_id)
        db.add(incident)
        db.flush()
        steps.append(f"INSERT incidents -> id {incident.incident_id}")
        db.add(Alert(device_id=device.device_id, incident_id=incident.incident_id, severity="info", source="manual",
                     message="[Transaction demo] linked alert"))
        db.flush()
        steps.append("INSERT alerts (linked to incident)")
        db.add(AuditLog(user_id=user.user_id, action="transaction_demo", entity_type="incident",
                        entity_id=str(incident.incident_id), details="commit demo"))
        db.flush()
        steps.append("INSERT audit_logs")
        if body.simulate_failure:
            steps.append("Simulated failure raised before COMMIT")
            raise RuntimeError("Simulated failure")
        db.commit()
        steps.append("COMMIT")
        outcome = "committed"
    except RuntimeError:
        db.rollback()
        steps.append("ROLLBACK")
        outcome = "rolled_back"
    after = _counts(db)
    return {"outcome": outcome, "steps": steps, "counts_before": before, "counts_after": after}
