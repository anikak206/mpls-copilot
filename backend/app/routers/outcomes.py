"""Outcomes CRUD. One outcome per prediction (enforced by the DB unique key + 409 here)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.database import get_db
from app.deps import get_current_user, require_role
from app.models import Outcome, Prediction
from app.schemas import OutcomeCreate, OutcomeOut, OutcomeResult, OutcomeUpdate

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


def _get_outcome_or_404(db: Session, outcome_id: int) -> Outcome:
    outcome = db.query(Outcome).filter(Outcome.outcome_id == outcome_id).first()
    if not outcome:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outcome not found")
    return outcome


@router.get("", response_model=list[OutcomeOut], summary="List outcomes")
def list_outcomes(
    prediction_id: Optional[int] = None,
    actual_result: Optional[OutcomeResult] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Outcome)
    if prediction_id is not None:
        q = q.filter(Outcome.prediction_id == prediction_id)
    if actual_result is not None:
        q = q.filter(Outcome.actual_result == actual_result.value)
    return q.order_by(Outcome.recorded_at.desc()).offset(skip).limit(limit).all()


@router.get("/{outcome_id}", response_model=OutcomeOut, summary="Get one outcome")
def get_outcome(outcome_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return _get_outcome_or_404(db, outcome_id)


@router.post("", response_model=OutcomeOut, status_code=status.HTTP_201_CREATED,
             summary="Record the actual outcome for a prediction")
def create_outcome(
    payload: OutcomeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    if not db.query(Prediction).filter(Prediction.prediction_id == payload.prediction_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    if db.query(Outcome).filter(Outcome.prediction_id == payload.prediction_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="An outcome is already recorded for this prediction")

    outcome = Outcome(**payload.model_dump(), recorded_by=current_user.user_id)
    db.add(outcome)
    db.flush()
    write_audit(db, current_user.user_id, "outcome", outcome.outcome_id, "create",
                {"prediction_id": outcome.prediction_id,
                 "actual_result": str(outcome.actual_result)})
    db.commit()
    db.refresh(outcome)
    return outcome


@router.put("/{outcome_id}", response_model=OutcomeOut, summary="Update an outcome")
def update_outcome(
    outcome_id: int,
    payload: OutcomeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    outcome = _get_outcome_or_404(db, outcome_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(outcome, field, value)
    write_audit(db, current_user.user_id, "outcome", outcome.outcome_id, "update",
                {"fields": sorted(data.keys())})
    db.commit()
    db.refresh(outcome)
    return outcome


@router.delete("/{outcome_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete an outcome (admin only)")
def delete_outcome(
    outcome_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    outcome = _get_outcome_or_404(db, outcome_id)
    write_audit(db, current_user.user_id, "outcome", outcome.outcome_id, "delete",
                {"prediction_id": outcome.prediction_id})
    db.delete(outcome)
    db.commit()