"""Audit trail — read-only, admin only. Rows are written by the write_audit() helper."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import require_role
from app.models import AuditLog
from app.schemas import AuditOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditOut], summary="Read the audit trail (admin only)")
def list_audit(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        q = q.filter(AuditLog.entity_id == entity_id)
    if user_id is not None:
        q = q.filter(AuditLog.user_id == user_id)
    return q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()