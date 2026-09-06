"""Alerts CRUD. Closing an alert stamps resolved_at automatically."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.database import get_db
from app.deps import get_current_user, require_role
from app.models import Alert, Device
from app.schemas import (
    AlertCreate,
    AlertOut,
    AlertUpdate,
    AlertSeverity,
    AlertStatus,
)


router = APIRouter(prefix="/alerts", tags=["alerts"])


def _get_alert_or_404(db: Session, alert_id: int) -> Alert:
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return alert


@router.get(
    "",
    response_model=list[AlertOut],
    summary="List alerts",
)
def list_alerts(
    device_id: Optional[int] = None,
    severity: Optional[AlertSeverity] = None,
    alert_status: Optional[AlertStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Alert)

    if device_id is not None:
        q = q.filter(Alert.device_id == device_id)

    if severity is not None:
        q = q.filter(Alert.severity == severity.value)

    if alert_status is not None:
        q = q.filter(Alert.status == alert_status.value)

    return (
        q.order_by(Alert.triggered_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/{alert_id}",
    response_model=AlertOut,
    summary="Get one alert",
)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return _get_alert_or_404(db, alert_id)


@router.post(
    "",
    response_model=AlertOut,
    status_code=status.HTTP_201_CREATED,
    summary="Raise an alert",
)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    if not db.query(Device).filter(
        Device.device_id == payload.device_id
    ).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    alert = Alert(**payload.model_dump())

    db.add(alert)
    db.flush()

    write_audit(
        db,
        current_user.user_id,
        "alert",
        alert.alert_id,
        "create",
        {
            "device_id": alert.device_id,
            "severity": str(alert.severity),
        },
    )

    db.commit()
    db.refresh(alert)

    return alert


@router.put(
    "/{alert_id}",
    response_model=AlertOut,
    summary="Update/acknowledge/close an alert",
)
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    alert = _get_alert_or_404(db, alert_id)

    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(alert, field, value)

    if alert.status == "closed" and alert.resolved_at is None:
        alert.resolved_at = func.now()
    elif alert.status != "closed":
        alert.resolved_at = None

    write_audit(
        db,
        current_user.user_id,
        "alert",
        alert.alert_id,
        "update",
        {
            "fields": sorted(data.keys()),
        },
    )

    db.commit()
    db.refresh(alert)

    return alert


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an alert (admin only)",
)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    alert = _get_alert_or_404(db, alert_id)

    write_audit(
        db,
        current_user.user_id,
        "alert",
        alert.alert_id,
        "delete",
        {
            "device_id": alert.device_id,
        },
    )

    db.delete(alert)
    db.commit()