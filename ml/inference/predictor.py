"""Local inference: validated features -> risk score, label, explanation. No network calls.

If the trained artifact is missing, a deterministic rule-based DEMO mode is used and every result is
labelled mode='demo' so it is never confused with model output.
"""
import math
from pathlib import Path

import joblib
import numpy as np

from ml.preprocessing.features import FEATURES, LABELS, validate_features
from ml.preprocessing.pipeline import transformed_feature_order

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "anomaly_model.joblib"
DEMO_LIMITS = {"cpu_util": 85, "mem_util": 90, "latency_ms": 100, "jitter_ms": 15, "packet_loss_pct": 1,
               "crc_errors": 50, "lsp_flaps": 2, "bgp_flaps": 2}


def risk_level(risk: float) -> str:
    return "low" if risk < 25 else "medium" if risk < 50 else "high" if risk < 75 else "critical"


def risk_label(risk: float) -> str:
    return "normal" if risk < 40 else "uncertain" if risk < 60 else "anomalous"


class AnomalyPredictor:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.artifact = joblib.load(model_path) if model_path.exists() else None
        self.mode = "model" if self.artifact else "demo"
        self.version = self.artifact["version"] if self.artifact else "rules-demo-1.0"

    def raw_scores(self, x: np.ndarray) -> np.ndarray:
        return -self.artifact["pipeline"].score_samples(x)

    def risk_from_raw(self, raw: float) -> float:
        c = self.artifact["calibration"]
        return round(100 / (1 + math.exp(-(raw - c["threshold"]) / c["width"])), 2)

    def _contributions(self, x: np.ndarray, values: dict):
        prep = self.artifact["pipeline"].named_steps["prep"]
        z = (prep.transform(x)[0] - np.array(self.artifact["baseline_mean"])) / np.array(self.artifact["baseline_std"])
        ranked = sorted(zip(transformed_feature_order(), z), key=lambda p: -abs(p[1]))
        return [{"feature": f, "label": LABELS[f], "value": values[f], "z_score": round(float(v), 2),
                 "direction": "high" if v > 0 else "low"} for f, v in ranked if abs(v) >= 2][:4]

    def _demo(self, values: dict):
        ratios = {f: values[f] / lim for f, lim in DEMO_LIMITS.items()}
        worst = max(ratios.values())
        risk = round(min(100.0, 50 * worst), 2)
        signals = [{"feature": f, "label": LABELS[f], "value": values[f], "z_score": round(r, 2),
                    "direction": "high"} for f, r in sorted(ratios.items(), key=lambda p: -p[1]) if r >= 0.8][:4]
        return risk, round(worst, 4), signals

    def predict(self, values: dict) -> dict:
        x = validate_features(values)
        clean = {f: float(x[0][i]) for i, f in enumerate(FEATURES)}
        if self.mode == "model":
            raw = float(self.raw_scores(x)[0])
            risk, signals = self.risk_from_raw(raw), self._contributions(x, clean)
        else:
            risk, raw, signals = self._demo(clean)
        label = risk_label(risk)
        return {"label": label, "risk_score": risk, "risk_level": risk_level(risk), "anomaly_score": round(raw, 4),
                "signals": signals, "explanation": explain(label, risk, signals, self.mode),
                "mode": self.mode, "model_version": self.version}


def explain(label, risk, signals, mode) -> str:
    prefix = "[DEMO MODE - rule-based, no trained model] " if mode == "demo" else ""
    if signals:
        parts = ", ".join(f"{s['label']} {s['direction']} ({s['value']:g}; deviation {s['z_score']:+.1f})"
                          for s in signals)
        body = f"Main contributing signals vs. the healthy baseline: {parts}."
    else:
        body = "No input signal deviates strongly from the healthy baseline."
    return f"{prefix}Classified as {label} with risk {risk:.1f}/100. {body}"


_predictor = None


def get_predictor() -> AnomalyPredictor:
    global _predictor
    if _predictor is None:
        _predictor = AnomalyPredictor()
    return _predictor
