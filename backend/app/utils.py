"""Shared helpers: pagination, audit logging, client IP."""
import json
from dataclasses import dataclass
from typing import Optional

from fastapi import Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditLog


@dataclass
class PageParams:
    page: int = Query(1, ge=1)
    page_size: int = Query(20, ge=1, le=200)


def paginate(db: Session, stmt, params: PageParams, serializer):
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.scalars(stmt.limit(params.page_size).offset((params.page - 1) * params.page_size)).unique().all()
    return {"items": [serializer(r) for r in rows], "total": total, "page": params.page,
            "page_size": params.page_size}


def client_ip(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    return (forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None))


def log_audit(db: Session, user_id, action: str, entity_type: str, entity_id=None, details=None, request=None):
    """Adds an audit row to the caller's transaction (committed together with the business change)."""
    db.add(AuditLog(user_id=user_id, action=action, entity_type=entity_type,
                    entity_id=None if entity_id is None else str(entity_id),
                    details=json.dumps(details, default=str) if isinstance(details, (dict, list)) else details,
                    ip_address=client_ip(request)))


def iso(value):
    return value.isoformat() if value else None
