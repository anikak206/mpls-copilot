"""Local ML module: validation, determinism, labels, explanations, recommendations, demo fallback."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.inference.predictor import AnomalyPredictor  # noqa: E402
from ml.inference.recommender import recommend  # noqa: E402
from ml.preprocessing.features import FeatureValidationError, check_frame  # noqa: E402
from ml.data.generator import generate_dataset  # noqa: E402

NORMAL = {"cpu_util": 35, "mem_util": 55, "latency_ms": 12, "jitter_ms": 1.2, "packet_loss_pct": 0.02,
          "throughput_mbps": 4200, "crc_errors": 0, "lsp_flaps": 0, "bgp_flaps": 0}
FLAPPING = {**NORMAL, "lsp_flaps": 9, "bgp_flaps": 5, "cpu_util": 70}


@pytest.fixture(scope="module")
def predictor():
    p = AnomalyPredictor()
    assert p.mode == "model", "trained artifact ml/models/anomaly_model.joblib is required"
    return p


def test_normal_sample(predictor):
    r = predictor.predict(NORMAL)
    assert r["label"] == "normal" and r["risk_score"] < 40 and r["risk_level"] in ("low", "medium")


def test_anomalous_sample_with_explanation(predictor):
    r = predictor.predict(FLAPPING)
    assert r["label"] == "anomalous" and r["risk_score"] >= 60
    assert r["signals"] and r["signals"][0]["feature"] in ("lsp_flaps", "bgp_flaps", "cpu_util")
    assert "contributing signals" in r["explanation"]


def test_deterministic(predictor):
    assert predictor.predict(FLAPPING) == predictor.predict(FLAPPING)


@pytest.mark.parametrize("bad", [{**NORMAL, "cpu_util": 101}, {**NORMAL, "latency_ms": -1},
                                 {k: v for k, v in NORMAL.items() if k != "jitter_ms"}, {**NORMAL, "mem_util": "x"}])
def test_input_validation(predictor, bad):
    with pytest.raises(FeatureValidationError):
        predictor.predict(bad)


def test_recommendation_mapping(predictor):
    rec = recommend(predictor.predict(FLAPPING))
    assert rec["action_code"] in ("REVIEW_LSP_STABILITY", "REVIEW_BGP_SESSIONS", "CHECK_CONTROL_PLANE_LOAD")
    assert "not a guaranteed resolution" in rec["rationale"]
    assert recommend(predictor.predict(NORMAL))["action_code"] == "CONTINUE_MONITORING"


def test_demo_mode_is_labelled(tmp_path):
    demo = AnomalyPredictor(model_path=tmp_path / "missing.joblib")
    r = demo.predict(FLAPPING)
    assert r["mode"] == "demo" and r["explanation"].startswith("[DEMO MODE")


def test_dataset_feature_consistency():
    df = check_frame(generate_dataset(n_normal=200, n_anomalous=40, seed=1))
    assert len(df) == 240 and set(df["label"]) == {0, 1}
