"""Evaluates the saved model on the held-out 30% split and writes ml/models/metrics.json.
Run: python -m ml.training.evaluate
"""
import json

import numpy as np
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from ml.inference.predictor import AnomalyPredictor
from ml.preprocessing.features import FEATURES
from ml.training.train import MODEL_DIR, split_dataset


def evaluate():
    _, test = split_dataset()
    predictor = AnomalyPredictor()
    if predictor.mode != "model":
        raise SystemExit("Model artifact missing: run python -m ml.training.train first")
    risks = np.array([predictor.risk_from_raw(a) for a in predictor.raw_scores(test[FEATURES].to_numpy(float))])
    y = test["label"].to_numpy()
    strict = (risks >= 60).astype(int)
    lenient = (risks >= 40).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, strict).ravel()
    per_type = {kind: float((risks[test["anomaly_type"].to_numpy() == kind] >= 60).mean())
                for kind in sorted(set(test["anomaly_type"])) if kind != "none"}
    metrics = {
        "evaluation_set": f"held-out synthetic split, n={len(test)} ({int(y.sum())} anomalous)",
        "roc_auc": round(float(roc_auc_score(y, risks)), 4),
        "anomalous_threshold_60": {
            "precision": round(float(precision_score(y, strict)), 4),
            "recall": round(float(recall_score(y, strict)), 4),
            "f1": round(float(f1_score(y, strict)), 4),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        },
        "including_uncertain_threshold_40": {
            "precision": round(float(precision_score(y, lenient)), 4),
            "recall": round(float(recall_score(y, lenient)), 4),
        },
        "uncertain_rate": round(float(((risks >= 40) & (risks < 60)).mean()), 4),
        "recall_by_anomaly_type": {k: round(v, 4) for k, v in per_type.items()},
        "note": "Synthetic-data metrics only; not evidence of real-world MPLS failure prediction accuracy.",
    }
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    evaluate()
