"""Engineer actions CRUD. The acting user is taken from the JWT, never from the payload."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.database import get_db
from app.deps import get_current_user, require_role
from app.models import EngineerAction, Prediction, Recommendation
from app.schemas import EngineerActionCreate, EngineerActionOut, EngineerActionUpdate

router = APIRouter(prefix="/actions", tags=["actions"])


def _get_action_or_404(db: Session, action_id: int) -> EngineerAction:
    action = db.query(EngineerAction).filter(EngineerAction.action_id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Engineer action not found")
    return action


def _check_refs(db: Session, prediction_id: int, recommendation_id: Optional[int]) -> None:
    if not db.query(Prediction).filter(Prediction.prediction_id == prediction_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    if recommendation_id is not None:
        rec = db.query(Recommendation).filter(
            Recommendation.recommendation_id == recommendation_id
        ).first()
        if not rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
        if rec.prediction_id != prediction_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Recommendation does not belong to this prediction")


@router.get("", response_model=list[EngineerActionOut], summary="List engineer actions")
def list_actions(
    prediction_id: Optional[int] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(EngineerAction)
    if prediction_id is not None:
        q = q.filter(EngineerAction.prediction_id == prediction_id)
    if user_id is not None:
        q = q.filter(EngineerAction.user_id == user_id)
    return q.order_by(EngineerAction.action_at.desc()).offset(skip).limit(limit).all()


@router.get("/{action_id}", response_model=EngineerActionOut, summary="Get one engineer action")
def get_action(action_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return _get_action_or_404(db, action_id)


@router.post("", response_model=EngineerActionOut, status_code=status.HTTP_201_CREATED,
             summary="Record an engineer action")
def create_action(
    payload: EngineerActionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    _check_refs(db, payload.prediction_id, payload.recommendation_id)

    action = EngineerAction(**payload.model_dump(), user_id=current_user.user_id)
    db.add(action)
    db.flush()
    write_audit(db, current_user.user_id, "engineer_action", action.action_id, "create",
                {"prediction_id": action.prediction_id,
                 "recommendation_id": action.recommendation_id})
    db.commit()
    db.refresh(action)
    return action


@router.put("/{action_id}", response_model=EngineerActionOut, summary="Update an engineer action")
def update_action(
    action_id: int,
    payload: EngineerActionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    action = _get_action_or_404(db, action_id)
    data = payload.model_dump(exclude_unset=True)
    if "recommendation_id" in data:
        _check_refs(db, action.prediction_id, data["recommendation_id"])

    for field, value in data.items():
        setattr(action, field, value)

    write_audit(db, current_user.user_id, "engineer_action", action.action_id, "update",
                {"fields": sorted(data.keys())})
    db.commit()
    db.refresh(action)
    return action


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete an engineer action (admin only)")
def delete_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    action = _get_action_or_404(db, action_id)
    write_audit(db, current_user.user_id, "engineer_action", action.action_id, "delete",
                {"prediction_id": action.prediction_id})
    db.delete(action)
    db.commit()