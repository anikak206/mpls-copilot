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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import require_role, get_current_user
from app.models import Device
from app.schemas import DeviceCreate, DeviceUpdate, DeviceOut

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
def list_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return db.query(Device).offset(skip).limit(limit).all()


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(
    payload: DeviceCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "network_engineer")),
):
    existing = db.query(Device).filter(Device.hostname == payload.hostname).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Hostname already exists")

    device = Device(**payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    # TODO (Person 1): write an audit_log row here once the audit helper exists (Phase 3/7)
    return device


@router.put("/{device_id}", response_model=DeviceOut)
def update_device(
    device_id: int,
    payload: DeviceUpdate,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin", "network_engineer")),
):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    db.delete(device)
    db.commit()
