"""Trains the local anomaly detector and writes ml/models/anomaly_model.joblib + metadata.json.

Method: IsolationForest fitted on NORMAL training samples only (semi-supervised novelty detection).
Risk calibration: raw anomaly score a = -score_samples(x). With t = 99th percentile and m = median of
a on normal training data, risk = 100 / (1 + exp(-(a - t) / w)), w = (t - m) / 3.
Run: python -m ml.training.train   (from the project root)
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from ml.data.generator import generate_dataset
from ml.preprocessing.features import FEATURES, check_frame
from ml.preprocessing.pipeline import build_preprocessor

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "anomaly_model.joblib"
META_PATH = MODEL_DIR / "metadata.json"
MODEL_VERSION = "iforest-synthetic-1.0"
SEED = 42


def split_dataset():
    df = check_frame(generate_dataset(seed=SEED))
    train, test = train_test_split(df, test_size=0.3, random_state=SEED, stratify=df["label"])
    return train, test


def train():
    train_df, _ = split_dataset()
    normal = train_df[train_df["label"] == 0][FEATURES].to_numpy(dtype=float)
    pipeline = Pipeline([
        ("prep", build_preprocessor()),
        ("model", IsolationForest(n_estimators=300, max_samples=512, contamination="auto", random_state=SEED)),
    ])
    pipeline.fit(normal)
    raw = -pipeline.score_samples(normal)
    threshold, median = float(np.percentile(raw, 99)), float(np.median(raw))
    transformed = pipeline.named_steps["prep"].transform(normal)
    artifact = {
        "pipeline": pipeline,
        "version": MODEL_VERSION,
        "features": FEATURES,
        "calibration": {"threshold": threshold, "median": median, "width": (threshold - median) / 3},
        "baseline_mean": transformed.mean(axis=0).tolist(),
        "baseline_std": transformed.std(axis=0).tolist(),
    }
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, MODEL_PATH)
    meta = {
        "model_version": MODEL_VERSION,
        "algorithm": "IsolationForest (n_estimators=300, max_samples=512), fitted on normal samples only",
        "training_data": "Synthetic MPLS telemetry from ml/data/generator.py (seed=42)",
        "training_normal_samples": int(len(normal)),
        "features": FEATURES,
        "calibration": artifact["calibration"],
        "label_rule": "risk>=60 anomalous; 40<=risk<60 uncertain; risk<40 normal",
        "risk_levels": "low<25<=medium<50<=high<75<=critical",
        "sklearn_version": sklearn.__version__,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Trained on synthetic data; it is a benchmark-style anomaly detector, not a validated MPLS failure predictor.",
            "Risk score is a calibrated anomaly score, not a probability of failure.",
            "Recommendations are advisory and must be reviewed by an engineer before action.",
        ],
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"Saved model to {MODEL_PATH}")
    return artifact


if __name__ == "__main__":
    train()
