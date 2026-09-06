"""Recommendations CRUD. Every recommendation is linked to a prediction."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.database import get_db
from app.deps import get_current_user, require_role
from app.models import Prediction, Recommendation
from app.schemas import RecPriority, RecommendationCreate, RecommendationOut, RecommendationUpdate

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _get_recommendation_or_404(db: Session, recommendation_id: int) -> Recommendation:
    rec = db.query(Recommendation).filter(Recommendation.recommendation_id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    return rec


@router.get("", response_model=list[RecommendationOut], summary="List recommendations")
def list_recommendations(
    prediction_id: Optional[int] = None,
    priority: Optional[RecPriority] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Recommendation)
    if prediction_id is not None:
        q = q.filter(Recommendation.prediction_id == prediction_id)
    if priority is not None:
        q = q.filter(Recommendation.priority == priority.value)
    return q.order_by(Recommendation.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{recommendation_id}", response_model=RecommendationOut, summary="Get one recommendation")
def get_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    return _get_recommendation_or_404(db, recommendation_id)


@router.post("", response_model=RecommendationOut, status_code=status.HTTP_201_CREATED,
             summary="Create a recommendation for a prediction")
def create_recommendation(
    payload: RecommendationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    if not db.query(Prediction).filter(Prediction.prediction_id == payload.prediction_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")

    rec = Recommendation(**payload.model_dump())
    db.add(rec)
    db.flush()
    write_audit(db, current_user.user_id, "recommendation", rec.recommendation_id, "create",
                {"prediction_id": rec.prediction_id, "priority": str(rec.priority)})
    db.commit()
    db.refresh(rec)
    return rec


@router.put("/{recommendation_id}", response_model=RecommendationOut, summary="Update a recommendation")
def update_recommendation(
    recommendation_id: int,
    payload: RecommendationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    rec = _get_recommendation_or_404(db, recommendation_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(rec, field, value)
    write_audit(db, current_user.user_id, "recommendation", rec.recommendation_id, "update",
                {"fields": sorted(data.keys())})
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/{recommendation_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a recommendation (admin only)")
def delete_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    rec = _get_recommendation_or_404(db, recommendation_id)
    write_audit(db, current_user.user_id, "recommendation", rec.recommendation_id, "delete",
                {"prediction_id": rec.prediction_id})
    db.delete(rec)
    db.commit()