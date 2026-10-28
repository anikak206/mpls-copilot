from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Device, Prediction, Site, Telemetry, User
from app.schemas import DeviceBase, DeviceUpdate, SiteIn
from app.security import ADMIN, ALL_ROLES, get_accessible_device, require_roles, scope_to_assigned
from app.serializers import device_out, prediction_out, telemetry_out
from app.utils import PageParams, log_audit, paginate

router = APIRouter(prefix="/api", tags=["Sites & Devices"])
admin_only = require_roles(ADMIN)
any_role = require_roles(*ALL_ROLES)


@router.get("/sites")
def list_sites(db: Session = Depends(get_db), _=Depends(any_role)):
    return [{"site_id": s.site_id, "name": s.name, "region": s.region, "address": s.address}
            for s in db.scalars(select(Site).order_by(Site.name))]


@router.post("/sites", status_code=201)
def create_site(body: SiteIn, request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    if db.scalar(select(Site).where(Site.name == body.name)):
        raise HTTPException(409, "Site name already exists")
    site = Site(**body.model_dump())
    db.add(site)
    db.flush()
    log_audit(db, admin.user_id, "site_created", "site", site.site_id, body.model_dump(), request)
    db.commit()
    return {"site_id": site.site_id, **body.model_dump()}


@router.get("/devices")
def list_devices(q: Optional[str] = None, status: Optional[str] = None, site_id: Optional[int] = None,
                 device_type: Optional[str] = None, params: PageParams = Depends(),
                 db: Session = Depends(get_db), user: User = Depends(any_role)):
    stmt = scope_to_assigned(select(Device).order_by(Device.hostname), user, Device.device_id)
    if q:
        stmt = stmt.where(or_(Device.hostname.contains(q), Device.mgmt_ip.contains(q), Device.model.contains(q),
                              Device.vendor.contains(q)))
    if status:
        stmt = stmt.where(Device.status == status)
    if site_id:
        stmt = stmt.where(Device.site_id == site_id)
    if device_type:
        stmt = stmt.where(Device.device_type == device_type)
    return paginate(db, stmt, params, device_out)


@router.get("/devices/{device_id}")
def get_device(device_id: int, db: Session = Depends(get_db), user: User = Depends(any_role)):
    device = get_accessible_device(db, user, device_id)
    recent = db.scalars(select(Telemetry).where(Telemetry.device_id == device_id)
                        .order_by(Telemetry.recorded_at.desc()).limit(24)).all()
    latest_pred = db.scalars(select(Prediction).join(Telemetry).where(Telemetry.device_id == device_id)
                             .order_by(Prediction.created_at.desc(), Prediction.prediction_id.desc()).limit(1)).first()
    open_alerts = db.scalar(select(func.count()).select_from(Alert)
                            .where(Alert.device_id == device_id, Alert.status != "resolved"))
    return {**device_out(device), "open_alerts": open_alerts, "recent_telemetry": [telemetry_out(t) for t in recent],
            "latest_prediction": prediction_out(latest_pred) if latest_pred else None}


def _check_refs(db: Session, data: dict):
    if data.get("site_id") and db.get(Site, data["site_id"]) is None:
        raise HTTPException(422, "site_id does not exist")
    eng = data.get("assigned_engineer_id")
    if eng:
        user = db.get(User, eng)
        if user is None or user.role.name != "Network Engineer":
            raise HTTPException(422, "assigned_engineer_id must reference a Network Engineer")


def _check_unique(db: Session, data: dict, exclude_id: Optional[int] = None):
    for field in ("hostname", "mgmt_ip"):
        if data.get(field):
            existing = db.scalar(select(Device).where(getattr(Device, field) == data[field]))
            if existing and existing.device_id != exclude_id:
                raise HTTPException(409, f"A device with this {field} already exists")


@router.post("/devices", status_code=201)
def create_device(body: DeviceBase, request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    data = body.model_dump()
    _check_refs(db, data)
    _check_unique(db, data)
    device = Device(**data)
    db.add(device)
    db.flush()
    log_audit(db, admin.user_id, "device_created", "device", device.device_id, data, request)
    db.commit()
    return device_out(db.get(Device, device.device_id))


@router.patch("/devices/{device_id}")
def update_device(device_id: int, body: DeviceUpdate, request: Request, db: Session = Depends(get_db),
                  admin: User = Depends(admin_only)):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(404, "Device not found")
    data = body.model_dump(exclude_unset=True)
    _check_refs(db, data)
    _check_unique(db, data, device_id)
    for key, value in data.items():
        setattr(device, key, value)
    log_audit(db, admin.user_id, "device_updated", "device", device_id, data, request)
    db.commit()
    db.refresh(device)
    return device_out(device)


@router.delete("/devices/{device_id}")
def delete_device(device_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(404, "Device not found")
    log_audit(db, admin.user_id, "device_deleted", "device", device_id, {"hostname": device.hostname}, request)
    db.delete(device)
    db.commit()
    return {"detail": "Device and its dependent operational records were deleted"}
