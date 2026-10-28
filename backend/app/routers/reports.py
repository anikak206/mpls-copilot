from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.exporters import to_csv, to_pdf
from app.models import Alert, AuditLog, Device, Incident, Prediction, Telemetry, User
from app.reports import REPORTS, fetch_report
from app.security import ADMIN, ALL_ROLES, AUDITOR, is_engineer, require_roles, scope_to_assigned
from app.serializers import alert_out, audit_out, prediction_out
from app.utils import PageParams, log_audit, paginate

router = APIRouter(prefix="/api", tags=["Dashboard, Reports & Audit"])
any_role = require_roles(*ALL_ROLES)
audit_roles = require_roles(ADMIN, AUDITOR)


def _grouped(db, column, user, device_col, base=None):
    stmt = scope_to_assigned(select(column, func.count()).group_by(column), user, device_col)
    if base is not None:
        stmt = stmt.where(base)
    return {k: v for k, v in db.execute(stmt).all()}


@router.get("/dashboard/summary")
def dashboard(db: Session = Depends(get_db), user: User = Depends(any_role)):
    hour = func.date_format(Telemetry.recorded_at, "%Y-%m-%d %H:00")
    series_stmt = scope_to_assigned(
        select(hour.label("hour"), func.avg(Telemetry.latency_ms), func.avg(Telemetry.packet_loss_pct),
               func.avg(Telemetry.cpu_util))
        .where(Telemetry.recorded_at >= func.date_sub(func.now(), literal_column("INTERVAL 7 DAY")))
        .group_by("hour").order_by("hour"), user, Telemetry.device_id)
    series = [{"hour": h[11:16] if h else h, "date": h, "latency": round(l or 0, 2), "loss": round(p or 0, 3),
               "cpu": round(c or 0, 2)} for h, l, p, c in db.execute(series_stmt).all()]
    avg_risk = db.scalar(scope_to_assigned(select(func.avg(Prediction.risk_score)).join(Telemetry), user,
                                           Telemetry.device_id))
    recent_preds = db.scalars(scope_to_assigned(select(Prediction).join(Telemetry), user, Telemetry.device_id)
                              .order_by(Prediction.created_at.desc(), Prediction.prediction_id.desc()).limit(6)).unique()
    recent_alerts = db.scalars(scope_to_assigned(select(Alert), user, Alert.device_id)
                               .order_by(Alert.created_at.desc(), Alert.alert_id.desc()).limit(6))
    activity = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.audit_id.desc()).limit(8)
    if is_engineer(user):
        activity = activity.where(AuditLog.user_id == user.user_id)
    return {
        "devices_by_status": _grouped(db, Device.status, user, Device.device_id),
        "open_alerts_by_severity": _grouped(db, Alert.severity, user, Alert.device_id, Alert.status != "resolved"),
        "incidents_by_status": _grouped(db, Incident.status, user, Incident.device_id),
        "risk_distribution": {k: v for k, v in db.execute(scope_to_assigned(
            select(Prediction.risk_level, func.count()).join(Telemetry).group_by(Prediction.risk_level),
            user, Telemetry.device_id)).all()},
        "label_distribution": {k: v for k, v in db.execute(scope_to_assigned(
            select(Prediction.label, func.count()).join(Telemetry).group_by(Prediction.label),
            user, Telemetry.device_id)).all()},
        "avg_risk": round(avg_risk or 0, 2),
        "telemetry_series": series,
        "recent_predictions": [prediction_out(p) for p in recent_preds],
        "recent_alerts": [alert_out(a) for a in recent_alerts],
        "recent_activity": [audit_out(a) for a in db.scalars(activity)],
    }


@router.get("/reports")
def list_reports(_=Depends(any_role)):
    return [{"key": k, "title": v} for k, v in REPORTS.items()]


def _filters(status, severity, label, risk_level, latest_risk_level, device_id, date_from, date_to, days):
    return {"status": status, "severity": severity, "label": label, "risk_level": risk_level,
            "latest_risk_level": latest_risk_level, "device_id": device_id,
            "date_from": date_from, "date_to": date_to, "days": days}


def _run(db, user, report, filters):
    if report not in REPORTS:
        raise HTTPException(404, "Unknown report")
    try:
        return fetch_report(db, user, report, filters)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.get("/reports/{report}")
def get_report(report: str, status: Optional[str] = None, severity: Optional[str] = None, label: Optional[str] = None,
               risk_level: Optional[str] = None, latest_risk_level: Optional[str] = None,
               device_id: Optional[int] = None, date_from: Optional[datetime] = None,
               date_to: Optional[datetime] = None, days: Optional[int] = None,
               db: Session = Depends(get_db), user: User = Depends(any_role)):
    f = _filters(status, severity, label, risk_level, latest_risk_level, device_id, date_from, date_to, days)
    columns, rows = _run(db, user, report, f)
    return {"report": report, "title": REPORTS[report], "columns": columns, "rows": rows, "count": len(rows)}


@router.get("/reports/{report}/export")
def export_report(report: str, request: Request, format: Literal["csv", "pdf"] = "csv",
                  status: Optional[str] = None, severity: Optional[str] = None, label: Optional[str] = None,
                  risk_level: Optional[str] = None, latest_risk_level: Optional[str] = None,
                  device_id: Optional[int] = None, date_from: Optional[datetime] = None,
                  date_to: Optional[datetime] = None, days: Optional[int] = None,
                  db: Session = Depends(get_db), user: User = Depends(any_role)):
    f = _filters(status, severity, label, risk_level, latest_risk_level, device_id, date_from, date_to, days)
    columns, rows = _run(db, user, report, f)
    log_audit(db, user.user_id, "report_exported", "report", report, {"format": format}, request)
    db.commit()
    if format == "csv":
        return Response(to_csv(columns, rows), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{report}.csv"'})
    return Response(to_pdf(REPORTS[report], columns, rows, f), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{report}.pdf"'})


def _audit_stmt(action, entity_type, user_id, date_from, date_to):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.audit_id.desc())
    for column, value in ((AuditLog.action, action), (AuditLog.entity_type, entity_type), (AuditLog.user_id, user_id)):
        if value:
            stmt = stmt.where(column == value)
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= date_to)
    return stmt


@router.get("/audit-logs")
def list_audit(action: Optional[str] = None, entity_type: Optional[str] = None, user_id: Optional[int] = None,
               date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
               params: PageParams = Depends(), db: Session = Depends(get_db), _=Depends(audit_roles)):
    return paginate(db, _audit_stmt(action, entity_type, user_id, date_from, date_to), params, audit_out)


@router.get("/audit-logs/actions")
def audit_actions(db: Session = Depends(get_db), _=Depends(audit_roles)):
    return sorted(db.scalars(select(AuditLog.action).distinct()).all())


@router.get("/audit-logs/export")
def export_audit(request: Request, action: Optional[str] = None, entity_type: Optional[str] = None,
                 user_id: Optional[int] = None, date_from: Optional[datetime] = None,
                 date_to: Optional[datetime] = None, db: Session = Depends(get_db), user: User = Depends(audit_roles)):
    rows = [audit_out(a) for a in db.scalars(_audit_stmt(action, entity_type, user_id, date_from, date_to).limit(5000))]
    columns = ["audit_id", "created_at", "user_email", "action", "entity_type", "entity_id", "details", "ip_address"]
    log_audit(db, user.user_id, "audit_exported", "audit_logs", None, {"rows": len(rows)}, request)
    db.commit()
    return Response(to_csv(columns, rows), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="audit_logs.csv"'})
