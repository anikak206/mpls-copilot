from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Alert, AuditLog, EngineerAction, Incident, User
from app.schemas import AlertCreate, AlertUpdate, IncidentCreate, IncidentUpdate
from app.security import ADMIN, ALL_ROLES, OPERATORS, get_accessible_device, require_roles, scope_to_assigned
from app.serializers import action_out, alert_out, audit_out, incident_out
from app.utils import PageParams, log_audit, paginate

router = APIRouter(prefix="/api", tags=["Alerts & Incidents"])
any_role = require_roles(*ALL_ROLES)
operators = require_roles(*OPERATORS)


@router.get("/alerts")
def list_alerts(status: Optional[str] = None, severity: Optional[str] = None, source: Optional[str] = None,
                device_id: Optional[int] = None, q: Optional[str] = None, params: PageParams = Depends(),
                db: Session = Depends(get_db), user: User = Depends(any_role)):
    stmt = scope_to_assigned(select(Alert).order_by(Alert.created_at.desc(), Alert.alert_id.desc()), user,
                             Alert.device_id)
    for column, value in ((Alert.status, status), (Alert.severity, severity), (Alert.source, source),
                          (Alert.device_id, device_id)):
        if value:
            stmt = stmt.where(column == value)
    if q:
        stmt = stmt.where(Alert.message.contains(q))
    return paginate(db, stmt, params, alert_out)


@router.post("/alerts", status_code=201)
def create_alert(body: AlertCreate, request: Request, db: Session = Depends(get_db), user: User = Depends(operators)):
    get_accessible_device(db, user, body.device_id)
    alert = Alert(**body.model_dump(), source="manual")
    db.add(alert)
    db.flush()
    log_audit(db, user.user_id, "alert_created", "alert", alert.alert_id, body.model_dump(), request)
    db.commit()
    return alert_out(db.get(Alert, alert.alert_id))


def _alert_for_user(db: Session, user: User, alert_id: int) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(404, "Alert not found")
    get_accessible_device(db, user, alert.device_id)
    return alert


@router.patch("/alerts/{alert_id}")
def update_alert(alert_id: int, body: AlertUpdate, request: Request, db: Session = Depends(get_db),
                 user: User = Depends(operators)):
    alert = _alert_for_user(db, user, alert_id)
    previous = alert.status
    alert.status = body.status
    if body.status == "acknowledged":
        alert.acknowledged_by = user.user_id
    alert.resolved_at = db.scalar(text("SELECT NOW()")) if body.status == "resolved" else None
    log_audit(db, user.user_id, "alert_status_changed", "alert", alert_id, f"{previous} -> {body.status}", request)
    db.commit()
    return alert_out(alert)


@router.post("/alerts/{alert_id}/escalate", status_code=201)
def escalate_alert(alert_id: int, db: Session = Depends(get_db), user: User = Depends(operators)):
    """Calls stored procedure sp_open_incident_from_alert (its own MySQL transaction)."""
    _alert_for_user(db, user, alert_id)
    db.close()
    with engine.connect() as conn:
        try:
            conn.exec_driver_sql("CALL sp_open_incident_from_alert(%s, %s, @new_incident)", (alert_id, user.user_id))
            incident_id = conn.exec_driver_sql("SELECT @new_incident").scalar()
            conn.commit()
        except DBAPIError as exc:
            conn.rollback()
            raise HTTPException(400, str(exc.orig.args[-1]) if exc.orig else "Escalation failed")
    with Session(engine) as fresh:
        return incident_out(fresh.get(Incident, incident_id))


@router.get("/incidents")
def list_incidents(status: Optional[str] = None, severity: Optional[str] = None, device_id: Optional[int] = None,
                   q: Optional[str] = None, params: PageParams = Depends(), db: Session = Depends(get_db),
                   user: User = Depends(any_role)):
    stmt = scope_to_assigned(select(Incident).order_by(Incident.opened_at.desc(), Incident.incident_id.desc()),
                             user, Incident.device_id)
    for column, value in ((Incident.status, status), (Incident.severity, severity), (Incident.device_id, device_id)):
        if value:
            stmt = stmt.where(column == value)
    if q:
        stmt = stmt.where(or_(Incident.title.contains(q), Incident.description.contains(q)))
    return paginate(db, stmt, params, incident_out)


def _incident_for_user(db: Session, user: User, incident_id: int) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(404, "Incident not found")
    get_accessible_device(db, user, incident.device_id)
    return incident


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db), user: User = Depends(any_role)):
    incident = _incident_for_user(db, user, incident_id)
    alerts = db.scalars(select(Alert).where(Alert.incident_id == incident_id)).all()
    actions = db.scalars(select(EngineerAction).where(EngineerAction.incident_id == incident_id)).unique().all()
    history = db.scalars(select(AuditLog).where(AuditLog.entity_type == "incident",
                                                AuditLog.entity_id == str(incident_id))
                         .order_by(AuditLog.created_at, AuditLog.audit_id)).all()
    return {**incident_out(incident), "alerts": [alert_out(a) for a in alerts],
            "actions": [action_out(a) for a in actions], "history": [audit_out(h) for h in history]}


@router.post("/incidents", status_code=201)
def create_incident(body: IncidentCreate, request: Request, db: Session = Depends(get_db),
                    user: User = Depends(operators)):
    get_accessible_device(db, user, body.device_id)
    incident = Incident(**body.model_dump(), opened_by=user.user_id)
    db.add(incident)
    db.flush()
    log_audit(db, user.user_id, "incident_created", "incident", incident.incident_id, {"title": body.title}, request)
    db.commit()
    return incident_out(db.get(Incident, incident.incident_id))


@router.patch("/incidents/{incident_id}")
def update_incident(incident_id: int, body: IncidentUpdate, request: Request, db: Session = Depends(get_db),
                    user: User = Depends(operators)):
    incident = _incident_for_user(db, user, incident_id)
    changes = body.model_dump(exclude_unset=True)
    if "assigned_to" in changes and changes["assigned_to"]:
        assignee = db.get(User, changes["assigned_to"])
        if assignee is None or assignee.role.name != "Network Engineer":
            raise HTTPException(422, "assigned_to must reference a Network Engineer")
    # Actor for trg_incident_status_audit (status changes are audited by the trigger only).
    db.execute(text("SET @app_user_id = :uid"), {"uid": user.user_id})
    for key, value in changes.items():
        setattr(incident, key, value)
    other = {k: v for k, v in changes.items() if k != "status"}
    if other:
        log_audit(db, user.user_id, "incident_updated", "incident", incident_id, other, request)
    db.commit()
    db.refresh(incident)
    return incident_out(incident)


@router.delete("/incidents/{incident_id}")
def delete_incident(incident_id: int, request: Request, db: Session = Depends(get_db),
                    user: User = Depends(require_roles(ADMIN))):
    incident = _incident_for_user(db, user, incident_id)
    log_audit(db, user.user_id, "incident_deleted", "incident", incident_id, {"title": incident.title}, request)
    db.delete(incident)
    db.commit()
    return {"detail": "Incident deleted"}
