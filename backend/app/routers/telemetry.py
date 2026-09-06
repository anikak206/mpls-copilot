"""Telemetry CRUD. POST is the ingestion endpoint; GET /devices/{id}/telemetry
(in devices.py) is the feed consumed by the AI module."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.database import get_db
from app.deps import get_current_user, require_role
from app.models import Device, Telemetry
from app.schemas import TelemetryCreate, TelemetryOut, TelemetryUpdate

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def _get_telemetry_or_404(db: Session, telemetry_id: int) -> Telemetry:
    row = db.query(Telemetry).filter(Telemetry.telemetry_id == telemetry_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemetry record not found")
    return row


@router.get("", response_model=list[TelemetryOut], summary="List telemetry records")
def list_telemetry(
    device_id: Optional[int] = None,
    metric_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Telemetry)
    if device_id is not None:
        q = q.filter(Telemetry.device_id == device_id)
    if metric_type:
        q = q.filter(Telemetry.metric_type == metric_type)
    return q.order_by(Telemetry.collected_at.desc()).offset(skip).limit(limit).all()


@router.get("/{telemetry_id}", response_model=TelemetryOut, summary="Get one telemetry record")
def get_telemetry(telemetry_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return _get_telemetry_or_404(db, telemetry_id)


@router.post("", response_model=TelemetryOut, status_code=status.HTTP_201_CREATED,
             summary="Ingest a telemetry record")
def create_telemetry(
    payload: TelemetryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    if not db.query(Device).filter(Device.device_id == payload.device_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    row = Telemetry(**payload.model_dump())
    db.add(row)
    db.flush()
    write_audit(db, current_user.user_id, "telemetry", row.telemetry_id, "create",
                {"device_id": row.device_id, "metric_type": row.metric_type})
    db.commit()
    db.refresh(row)
    return row


@router.put("/{telemetry_id}", response_model=TelemetryOut, summary="Update a telemetry record")
def update_telemetry(
    telemetry_id: int,
    payload: TelemetryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    row = _get_telemetry_or_404(db, telemetry_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    write_audit(db, current_user.user_id, "telemetry", row.telemetry_id, "update",
                {"fields": sorted(payload.model_dump(exclude_unset=True).keys())})
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{telemetry_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a telemetry record (admin only)")
def delete_telemetry(
    telemetry_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    row = _get_telemetry_or_404(db, telemetry_id)
    write_audit(db, current_user.user_id, "telemetry", row.telemetry_id, "delete",
                {"device_id": row.device_id, "metric_type": row.metric_type})
    db.delete(row)
    db.commit()