"""Prediction workflow shared by the API and the seed script (caller owns the transaction)."""
from sqlalchemy.orm import Session

from app.models import Alert, Prediction, Recommendation, Telemetry
from app.serializers import FEATURE_COLS
from ml.inference.predictor import get_predictor
from ml.inference.recommender import recommend


def run_prediction(db: Session, sample: Telemetry, user_id) -> Prediction:
    result = get_predictor().predict({c: getattr(sample, c) for c in FEATURE_COLS})
    prediction = Prediction(telemetry_id=sample.telemetry_id, model_version=result["model_version"],
                            mode=result["mode"], label=result["label"], anomaly_score=result["anomaly_score"],
                            risk_score=result["risk_score"], risk_level=result["risk_level"],
                            explanation=result["explanation"], requested_by=user_id)
    db.add(prediction)
    db.flush()
    db.add(Recommendation(prediction_id=prediction.prediction_id, **recommend(result)))
    if result["label"] == "anomalous":
        top = result["signals"][0]["label"] if result["signals"] else "multiple signals"
        db.add(Alert(device_id=sample.device_id, telemetry_id=sample.telemetry_id,
                     prediction_id=prediction.prediction_id, source="ml",
                     severity="critical" if result["risk_level"] == "critical" else "major",
                     message=f"ML anomaly detected (risk {result['risk_score']:.1f}); main signal: {top}"))
    db.flush()
    return prediction
