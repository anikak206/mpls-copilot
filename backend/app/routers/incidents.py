"""Incidents CRUD. opened_by is set to the caller; closing stamps closed_at."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.database import get_db
from app.deps import get_current_user, require_role
from app.models import Alert, Device, Incident
from app.schemas import IncidentCreate, IncidentOut, IncidentUpdate, IncidentStatus

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _get_incident_or_404(db: Session, incident_id: int) -> Incident:
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


def _check_refs(db: Session, device_id: int, alert_id: Optional[int]) -> None:
    if not db.query(Device).filter(Device.device_id == device_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if alert_id is not None and not db.query(Alert).filter(Alert.alert_id == alert_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")


@router.get("", response_model=list[IncidentOut], summary="List incidents")
def list_incidents(
    device_id: Optional[int] = None,
    incident_status: Optional[IncidentStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Incident)
    if device_id is not None:
        q = q.filter(Incident.device_id == device_id)
    if incident_status is not None:
        q = q.filter(Incident.status == incident_status.value)
    return q.order_by(Incident.opened_at.desc()).offset(skip).limit(limit).all()


@router.get("/{incident_id}", response_model=IncidentOut, summary="Get one incident")
def get_incident(incident_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return _get_incident_or_404(db, incident_id)


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED,
             summary="Open an incident")
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    _check_refs(db, payload.device_id, payload.alert_id)

    incident = Incident(**payload.model_dump(), opened_by=current_user.user_id)
    db.add(incident)
    db.flush()
    write_audit(db, current_user.user_id, "incident", incident.incident_id, "create",
                {"device_id": incident.device_id, "title": incident.title})
    db.commit()
    db.refresh(incident)
    return incident


@router.put("/{incident_id}", response_model=IncidentOut, summary="Update an incident")
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    incident = _get_incident_or_404(db, incident_id)
    data = payload.model_dump(exclude_unset=True)
    if "alert_id" in data and data["alert_id"] is not None:
        _check_refs(db, incident.device_id, data["alert_id"])

    for field, value in data.items():
        setattr(incident, field, value)

    if incident.status in ("resolved", "closed") and incident.closed_at is None:
        incident.closed_at = func.now()
    elif incident.status in ("open", "in_progress"):
        incident.closed_at = None

    write_audit(db, current_user.user_id, "incident", incident.incident_id, "update",
                {"fields": sorted(data.keys())})
    db.commit()
    db.refresh(incident)
    return incident


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete an incident (admin only)")
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    incident = _get_incident_or_404(db, incident_id)
    write_audit(db, current_user.user_id, "incident", incident.incident_id, "delete",
                {"title": incident.title})
    db.delete(incident)
    db.commit()