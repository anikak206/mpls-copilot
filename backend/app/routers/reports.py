"""Aggregated reports for the dashboard: per-device health and incident summary.
No new tables — these are read-only queries over existing data."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import Alert, Device, EngineerAction, Incident, Outcome, Prediction

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/device-health", summary="Per-device health: open/critical alerts, open incidents, latest prediction risk")
def device_health(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    report = []
    for device in db.query(Device).order_by(Device.hostname).all():
        open_alerts = db.query(func.count(Alert.alert_id)).filter(
            Alert.device_id == device.device_id, Alert.status != "closed"
        ).scalar()
        critical_alerts = db.query(func.count(Alert.alert_id)).filter(
            Alert.device_id == device.device_id,
            Alert.severity == "critical",
            Alert.status != "closed",
        ).scalar()
        open_incidents = db.query(func.count(Incident.incident_id)).filter(
            Incident.device_id == device.device_id,
            Incident.status.in_(["open", "in_progress"]),
        ).scalar()
        latest = db.query(Prediction).filter(
            Prediction.device_id == device.device_id
        ).order_by(Prediction.predicted_at.desc()).first()

        report.append({
            "device_id": device.device_id,
            "hostname": device.hostname,
            "site": device.site,
            "is_active": device.is_active,
            "open_alerts": open_alerts,
            "critical_alerts": critical_alerts,
            "open_incidents": open_incidents,
            "latest_risk_level": str(latest.risk_level) if latest else None,
            "latest_risk_score": float(latest.risk_score) if latest else None,
            "latest_prediction_at": latest.predicted_at.isoformat()
            if latest and latest.predicted_at else None,
        })
    return report


@router.get("/incident-summary", summary="Totals: incidents by status, predictions by risk, outcomes by result")
def incident_summary(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    incidents_by_status = {
        str(s): c for s, c in db.query(Incident.status, func.count()).group_by(Incident.status).all()
    }
    predictions_by_risk = {
        str(s): c for s, c in db.query(Prediction.risk_level, func.count()).group_by(Prediction.risk_level).all()
    }
    outcomes_by_result = {
        str(s): c for s, c in db.query(Outcome.actual_result, func.count()).group_by(Outcome.actual_result).all()
    }
    return {
        "total_incidents": sum(incidents_by_status.values()),
        "incidents_by_status": incidents_by_status,
        "predictions_by_risk_level": predictions_by_risk,
        "outcomes_by_result": outcomes_by_result,
        "open_alerts": db.query(func.count(Alert.alert_id)).filter(Alert.status != "closed").scalar(),
        "engineer_actions_logged": db.query(func.count(EngineerAction.action_id)).scalar(),
    }