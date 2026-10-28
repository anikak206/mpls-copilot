# ML Model Card — Local Network Anomaly Detector

| Item | Value |
|---|---|
| Model | IsolationForest (scikit-learn, 300 trees, max_samples 512), fitted on **normal samples only** |
| Version | `iforest-synthetic-1.0` (`ml/models/metadata.json`) |
| Artifact | `ml/models/anomaly_model.joblib` (local file; retrain: `python -m ml.training.train`) |
| Features (9) | cpu_util, mem_util, latency_ms, jitter_ms, packet_loss_pct, throughput_mbps, crc_errors, lsp_flaps, bgp_flaps |
| Preprocessing | log1p on heavy-tailed features, StandardScaler; feature-consistency checks (`ml/preprocessing/features.py`) |
| Training data | **Synthetic** MPLS-style telemetry from `ml/data/generator.py` (seed 42): 8 000 normal + 800 anomalous across 4 fault patterns (congestion, link degradation, control-plane instability, resource exhaustion) |
| Runtime | Local CPU inference; no external API |

## Risk scoring method
raw anomaly score `a = -score_samples(x)`. With `t` = 99th percentile and `m` = median of `a` over normal training data and `w = (t − m)/3`:
`risk = 100 / (1 + exp(−(a − t)/w))`.
Label: risk ≥ 60 → **anomalous**; 40–60 → **uncertain**; < 40 → **normal**. Level: low < 25 ≤ medium < 50 ≤ high < 75 ≤ critical.

## Explanation
Each feature is transformed and compared to the healthy baseline mean/std; features with |z| ≥ 2 are reported (top 4) as contributing signals. The dominant signal selects the advisory recommendation (`ml/inference/recommender.py`), which always carries a "not a guaranteed resolution" disclaimer.

## Evaluation (held-out 30 % synthetic split, computed by `python -m ml.training.evaluate`)
Actual output in `ml/models/metrics.json`:
- ROC-AUC 0.9928
- Anomalous threshold (risk ≥ 60): precision 0.9565, recall 0.6417, F1 0.7681 (TN 2393, FP 7, FN 86, TP 154)
- Including uncertain (risk ≥ 40): precision 0.8254, recall 0.8667
- Recall by fault type: congestion 0.82, control-plane instability 0.87, link degradation 0.79, **resource exhaustion 0.05**

## Limitations (honest)
- Trained and evaluated on synthetic data only; these metrics do **not** demonstrate accuracy on real MPLS networks.
- Not a failure predictor; the risk score is a calibrated anomaly score, not a probability.
- Resource-exhaustion anomalies (high CPU + memory only) are rarely detected at the 60 threshold — a known weakness.
- Subtle anomalies are deliberately included, which lowers recall.
- **UNSW-NB15:** an optional pipeline is provided (`ml/training/train_unsw.py`) with a documented approximate feature mapping. It was **not executed** (dataset not available offline). UNSW-NB15 is an intrusion-detection benchmark, not MPLS failure data.
- **Demo mode:** if the artifact is missing, a deterministic rule-based mode is used and every result is labelled `mode=demo` and "[DEMO MODE]".
