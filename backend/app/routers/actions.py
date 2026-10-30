from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EngineerAction, Incident, Outcome, Recommendation, User
from app.schemas import ActionCreate, OutcomeIn
from app.security import ALL_ROLES, OPERATORS, get_accessible_device, require_roles, scope_to_assigned
from app.serializers import action_out
from app.utils import PageParams, log_audit, paginate

router = APIRouter(prefix="/api", tags=["Engineer Actions & Outcomes"])
operators = require_roles(*OPERATORS)


@router.get("/actions")
def list_actions(device_id: Optional[int] = None, action_type: Optional[str] = None,
                 has_outcome: Optional[bool] = None, params: PageParams = Depends(),
                 db: Session = Depends(get_db), user: User = Depends(require_roles(*ALL_ROLES))):
    stmt = scope_to_assigned(select(EngineerAction).order_by(EngineerAction.performed_at.desc(),
                                                             EngineerAction.action_id.desc()),
                             user, EngineerAction.device_id)
    if device_id:
        stmt = stmt.where(EngineerAction.device_id == device_id)
    if action_type:
        stmt = stmt.where(EngineerAction.action_type == action_type)
    if has_outcome is not None:
        linked = select(Outcome.action_id)
        stmt = stmt.where(EngineerAction.action_id.in_(linked) if has_outcome else EngineerAction.action_id.not_in(linked))
    return paginate(db, stmt, params, action_out)


@router.post("/actions", status_code=201)
def create_action(body: ActionCreate, request: Request, db: Session = Depends(get_db), user: User = Depends(operators)):
    """Action and optional outcome are written in one transaction."""
    get_accessible_device(db, user, body.device_id)
    if body.recommendation_id:
        rec = db.get(Recommendation, body.recommendation_id)
        if rec is None or rec.prediction.telemetry.device_id != body.device_id:
            raise HTTPException(422, "recommendation_id does not belong to this device")
    if body.incident_id:
        incident = db.get(Incident, body.incident_id)
        if incident is None or incident.device_id != body.device_id:
            raise HTTPException(422, "incident_id does not belong to this device")
    try:
        action = EngineerAction(**body.model_dump(exclude={"outcome"}), engineer_id=user.user_id)
        db.add(action)
        db.flush()
        if body.outcome:
            db.add(Outcome(action_id=action.action_id, recorded_by=user.user_id, **body.outcome.model_dump()))
        log_audit(db, user.user_id, "action_recorded", "engineer_action", action.action_id,
                  {"action_type": body.action_type, "outcome": body.outcome.result if body.outcome else None}, request)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.expire_all()
    return action_out(db.get(EngineerAction, action.action_id))


@router.post("/actions/{action_id}/outcome", status_code=201)
def record_outcome(action_id: int, body: OutcomeIn, request: Request, db: Session = Depends(get_db),
                   user: User = Depends(operators)):
    action = db.get(EngineerAction, action_id)
    if action is None:
        raise HTTPException(404, "Action not found")
    get_accessible_device(db, user, action.device_id)
    if action.outcome is not None:
        raise HTTPException(409, "An outcome is already recorded for this action")
    db.add(Outcome(action_id=action_id, recorded_by=user.user_id, **body.model_dump()))
    log_audit(db, user.user_id, "outcome_recorded", "engineer_action", action_id, {"result": body.result}, request)
    db.commit()
    db.expire_all()
    return action_out(db.get(EngineerAction, action_id))
