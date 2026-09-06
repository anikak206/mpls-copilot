"""
Devices CRUD — treat this file as the pattern to copy for telemetry, alerts,
incidents, predictions, recommendations, engineer_actions, and outcomes routers.

Pattern per resource:
  GET    /resource          -> list (role: any authenticated user)
  GET    /resource/{id}     -> get one
  POST   /resource           -> create (role: admin, network_engineer)
  PUT    /resource/{id}      -> update (role: admin, network_engineer)
  DELETE /resource/{id}      -> delete (role: admin only)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.database import get_db
from app.deps import require_role, get_current_user
from app.models import Device, Telemetry
from app.schemas import DeviceCreate, DeviceUpdate, DeviceOut, TelemetryOut

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut], summary="List devices")
def list_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return db.query(Device).offset(skip).limit(limit).all()


@router.get("/{device_id}", response_model=DeviceOut, summary="Get one device")
def get_device(device_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.get("/{device_id}/telemetry", response_model=list[TelemetryOut],
            summary="Telemetry feed for one device (consumed by the AI module)")
def device_telemetry_feed(
    device_id: int,
    metric_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    q = db.query(Telemetry).filter(Telemetry.device_id == device_id)
    if metric_type:
        q = q.filter(Telemetry.metric_type == metric_type)
    return q.order_by(Telemetry.collected_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED,
             summary="Register a device")
def create_device(
    payload: DeviceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    existing = db.query(Device).filter(Device.hostname == payload.hostname).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Hostname already exists")

    device = Device(**payload.model_dump())
    db.add(device)
    db.flush()
    write_audit(db, current_user.user_id, "device", device.device_id, "create",
                {"hostname": device.hostname})
    db.commit()
    db.refresh(device)
    return device


@router.put("/{device_id}", response_model=DeviceOut, summary="Update a device")
def update_device(
    device_id: int,
    payload: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    data = payload.model_dump(exclude_unset=True)
    new_hostname = data.get("hostname")
    if new_hostname and new_hostname != device.hostname:
        clash = db.query(Device).filter(
            Device.hostname == new_hostname, Device.device_id != device_id
        ).first()
        if clash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Hostname already exists")

    for field, value in data.items():
        setattr(device, field, value)

    write_audit(db, current_user.user_id, "device", device.device_id, "update",
                {"fields": sorted(data.keys())})
    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a device (admin only)")
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    write_audit(db, current_user.user_id, "device", device.device_id, "delete",
                {"hostname": device.hostname})
    db.delete(device)
    db.commit()