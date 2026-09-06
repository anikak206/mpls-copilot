"""Predictions API. POST is the ingestion endpoint the AI module writes to
(risk_score, risk_level, contributing_factors JSON)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.database import get_db
from app.deps import get_current_user, require_role
from app.models import Device, Incident, Prediction, Recommendation
from app.schemas import (
    PredictionCreate, PredictionOut, PredictionUpdate, RecommendationOut, RiskLevel,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])


def _get_prediction_or_404(db: Session, prediction_id: int) -> Prediction:
    pred = db.query(Prediction).filter(Prediction.prediction_id == prediction_id).first()
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    return pred


def _check_refs(db: Session, device_id: int, incident_id: Optional[int]) -> None:
    if not db.query(Device).filter(Device.device_id == device_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if incident_id is not None and not db.query(Incident).filter(
        Incident.incident_id == incident_id
    ).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")


@router.get("", response_model=list[PredictionOut], summary="List predictions")
def list_predictions(
    device_id: Optional[int] = None,
    risk_level: Optional[RiskLevel] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Prediction)
    if device_id is not None:
        q = q.filter(Prediction.device_id == device_id)
    if risk_level is not None:
        q = q.filter(Prediction.risk_level == risk_level.value)
    return q.order_by(Prediction.predicted_at.desc()).offset(skip).limit(limit).all()


@router.get("/{prediction_id}", response_model=PredictionOut, summary="Get one prediction")
def get_prediction(prediction_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return _get_prediction_or_404(db, prediction_id)


@router.get("/{prediction_id}/recommendations", response_model=list[RecommendationOut],
            summary="List recommendations linked to a prediction")
def list_prediction_recommendations(
    prediction_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    _get_prediction_or_404(db, prediction_id)
    return db.query(Recommendation).filter(Recommendation.prediction_id == prediction_id).all()


@router.post("", response_model=PredictionOut, status_code=status.HTTP_201_CREATED,
             summary="Store a new AI prediction (ingestion endpoint)")
def create_prediction(
    payload: PredictionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    _check_refs(db, payload.device_id, payload.incident_id)

    pred = Prediction(**payload.model_dump())
    db.add(pred)
    db.flush()
    write_audit(db, current_user.user_id, "prediction", pred.prediction_id, "create",
                {"device_id": pred.device_id, "risk_level": str(pred.risk_level),
                 "model_version": pred.model_version})
    db.commit()
    db.refresh(pred)
    return pred


@router.put("/{prediction_id}", response_model=PredictionOut, summary="Update a prediction")
def update_prediction(
    prediction_id: int,
    payload: PredictionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "network_engineer")),
):
    pred = _get_prediction_or_404(db, prediction_id)
    data = payload.model_dump(exclude_unset=True)
    if "incident_id" in data and data["incident_id"] is not None:
        _check_refs(db, pred.device_id, data["incident_id"])

    for field, value in data.items():
        setattr(pred, field, value)

    write_audit(db, current_user.user_id, "prediction", pred.prediction_id, "update",
                {"fields": sorted(data.keys())})
    db.commit()
    db.refresh(pred)
    return pred


@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a prediction (admin only)")
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    pred = _get_prediction_or_404(db, prediction_id)
    write_audit(db, current_user.user_id, "prediction", pred.prediction_id, "delete",
                {"device_id": pred.device_id})
    db.delete(pred)
    db.commit()