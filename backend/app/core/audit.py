"""Audit-trail helper. Call write_audit() before db.commit() so the audit row
is written in the same transaction as the change it describes."""

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit(
    db: Session,
    user_id: Optional[int],
    entity_type: str,
    entity_id: int,
    action: str,
    details: Optional[Any] = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details,
        )
    )