from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Telemetry, User
from app.schemas import TelemetryIn
from app.security import ALL_ROLES, OPERATORS, get_accessible_device, require_roles, scope_to_assigned
from app.serializers import alert_out, telemetry_out
from app.utils import PageParams, log_audit, paginate

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])


@router.get("")
def list_telemetry(device_id: Optional[int] = None, source: Optional[str] = None,
                   date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
                   min_loss: Optional[float] = None, params: PageParams = Depends(),
                   db: Session = Depends(get_db), user: User = Depends(require_roles(*ALL_ROLES))):
    stmt = scope_to_assigned(select(Telemetry).order_by(Telemetry.recorded_at.desc(), Telemetry.telemetry_id.desc()),
                             user, Telemetry.device_id)
    if device_id:
        stmt = stmt.where(Telemetry.device_id == device_id)
    if source:
        stmt = stmt.where(Telemetry.source == source)
    if date_from:
        stmt = stmt.where(Telemetry.recorded_at >= date_from)
    if date_to:
        stmt = stmt.where(Telemetry.recorded_at <= date_to)
    if min_loss is not None:
        stmt = stmt.where(Telemetry.packet_loss_pct >= min_loss)
    return paginate(db, stmt, params, telemetry_out)


@router.post("", status_code=201)
def create_telemetry(body: TelemetryIn, request: Request, db: Session = Depends(get_db),
                     user: User = Depends(require_roles(*OPERATORS))):
    get_accessible_device(db, user, body.device_id)
    data = body.model_dump(exclude_none=True)
    sample = Telemetry(**data, source="manual", recorded_by=user.user_id)
    db.add(sample)
    db.flush()
    log_audit(db, user.user_id, "telemetry_recorded", "telemetry", sample.telemetry_id,
              {"device_id": body.device_id}, request)
    db.commit()
    # Alerts created by trg_telemetry_threshold_alert inside the same INSERT.
    raised = db.scalars(select(Alert).where(Alert.telemetry_id == sample.telemetry_id)).all()
    return {**telemetry_out(db.get(Telemetry, sample.telemetry_id)), "trigger_alerts": [alert_out(a) for a in raised]}


@router.get("/stats")
def telemetry_stats(device_id: Optional[int] = None, db: Session = Depends(get_db),
                    user: User = Depends(require_roles(*ALL_ROLES))):
    stmt = scope_to_assigned(select(func.count(), func.avg(Telemetry.cpu_util), func.avg(Telemetry.latency_ms),
                                    func.avg(Telemetry.packet_loss_pct), func.max(Telemetry.recorded_at)),
                             user, Telemetry.device_id)
    if device_id:
        stmt = stmt.where(Telemetry.device_id == device_id)
    count, cpu, lat, loss, last = db.execute(stmt).one()
    return {"samples": count, "avg_cpu": round(cpu or 0, 2), "avg_latency": round(lat or 0, 2),
            "avg_loss": round(loss or 0, 3), "last_sample": last.isoformat() if last else None}
