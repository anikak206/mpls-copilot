import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Prediction, Recommendation, Telemetry, User
from app.prediction_service import run_prediction
from app.schemas import PredictRequest
from app.security import ALL_ROLES, OPERATORS, get_accessible_device, require_roles, scope_to_assigned
from app.serializers import prediction_out, recommendation_out
from app.utils import PageParams, log_audit, paginate
from ml.inference.predictor import get_predictor
from ml.training.train import META_PATH, MODEL_DIR

router = APIRouter(prefix="/api", tags=["Predictions & Recommendations"])
any_role = require_roles(*ALL_ROLES)


@router.post("/predictions/run", status_code=201)
def run(body: PredictRequest, request: Request, db: Session = Depends(get_db),
        user: User = Depends(require_roles(*OPERATORS))):
    """One transaction: [optional telemetry insert] + prediction + recommendation + [ML alert] + audit."""
    try:
        if body.telemetry_id:
            sample = db.get(Telemetry, body.telemetry_id)
            if sample is None:
                raise HTTPException(404, "Telemetry sample not found")
            get_accessible_device(db, user, sample.device_id)
        elif body.device_id and body.features:
            get_accessible_device(db, user, body.device_id)
            sample = Telemetry(device_id=body.device_id, source="manual", recorded_by=user.user_id,
                               **body.features.model_dump())
            db.add(sample)
            db.flush()
        else:
            raise HTTPException(422, "Provide telemetry_id, or device_id with features")
        prediction = run_prediction(db, sample, user.user_id)
        log_audit(db, user.user_id, "prediction_run", "prediction", prediction.prediction_id,
                  {"telemetry_id": sample.telemetry_id, "label": prediction.label, "risk": prediction.risk_score},
                  request)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return prediction_out(db.get(Prediction, prediction.prediction_id))


@router.get("/predictions")
def list_predictions(label: Optional[str] = None, risk_level: Optional[str] = None, device_id: Optional[int] = None,
                     params: PageParams = Depends(), db: Session = Depends(get_db), user: User = Depends(any_role)):
    stmt = scope_to_assigned(select(Prediction).join(Telemetry)
                             .order_by(Prediction.created_at.desc(), Prediction.prediction_id.desc()),
                             user, Telemetry.device_id)
    if label:
        stmt = stmt.where(Prediction.label == label)
    if risk_level:
        stmt = stmt.where(Prediction.risk_level == risk_level)
    if device_id:
        stmt = stmt.where(Telemetry.device_id == device_id)
    return paginate(db, stmt, params, prediction_out)


@router.get("/predictions/{prediction_id}")
def get_prediction(prediction_id: int, db: Session = Depends(get_db), user: User = Depends(any_role)):
    prediction = db.get(Prediction, prediction_id)
    if prediction is None:
        raise HTTPException(404, "Prediction not found")
    get_accessible_device(db, user, prediction.telemetry.device_id)
    return prediction_out(prediction)


@router.get("/recommendations")
def list_recommendations(priority: Optional[str] = None, action_code: Optional[str] = None,
                         params: PageParams = Depends(), db: Session = Depends(get_db), user: User = Depends(any_role)):
    stmt = scope_to_assigned(select(Recommendation).join(Prediction).join(Telemetry)
                             .order_by(Recommendation.created_at.desc(), Recommendation.recommendation_id.desc()),
                             user, Telemetry.device_id)
    if priority:
        stmt = stmt.where(Recommendation.priority == priority)
    if action_code:
        stmt = stmt.where(Recommendation.action_code == action_code)

    def out(r):
        p = r.prediction
        return {**recommendation_out(r), "hostname": p.telemetry.device.hostname, "device_id": p.telemetry.device_id,
                "label": p.label, "risk_score": p.risk_score, "risk_level": p.risk_level}
    return paginate(db, stmt, params, out)


@router.get("/ml/model-info")
def model_info(_=Depends(any_role)):
    predictor = get_predictor()
    meta = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}
    metrics_path = MODEL_DIR / "metrics.json"
    metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else None
    return {"mode": predictor.mode, "model_version": predictor.version, "metadata": meta, "metrics": metrics,
            "runtime": "Local scikit-learn inference; no external AI API is called."}
