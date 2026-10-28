"""Deterministic synthetic MPLS telemetry generator.

No public dataset of real MPLS device failures was available in this environment, so the model is
trained on documented synthetic data: a healthy operating envelope plus four injected fault patterns
(congestion, link degradation, control-plane instability, resource exhaustion). Metrics computed on
this data describe behaviour on the synthetic distribution only, not on real production networks.
"""
import numpy as np
import pandas as pd

from ml.preprocessing.features import FEATURES

ANOMALY_TYPES = ["congestion", "link_degradation", "control_plane_instability", "resource_exhaustion"]


def normal_samples(n: int, rng: np.random.Generator, load: float = 1.0) -> pd.DataFrame:
    df = pd.DataFrame({
        "cpu_util": np.clip(rng.normal(35 * load, 9, n), 2, 80),
        "mem_util": np.clip(rng.normal(55, 7, n), 20, 82),
        "latency_ms": np.clip(rng.gamma(6, 2.2, n), 2, 60),
        "jitter_ms": np.clip(rng.gamma(2, 0.7, n), 0.05, 8),
        "packet_loss_pct": np.clip(rng.exponential(0.04, n), 0, 0.5),
        "throughput_mbps": np.clip(rng.normal(4200 * load, 900, n), 300, 9000),
        "crc_errors": rng.poisson(0.6, n),
        "lsp_flaps": rng.poisson(0.05, n),
        "bgp_flaps": rng.poisson(0.02, n),
    })
    return df[FEATURES]


def inject(df: pd.DataFrame, kind: str, rng: np.random.Generator, severity: np.ndarray) -> pd.DataFrame:
    """Applies a fault pattern; severity in [0.25, 1] makes some anomalies deliberately subtle."""
    out = df.copy()
    s = severity
    if kind == "congestion":
        out["latency_ms"] *= 1 + 6 * s
        out["jitter_ms"] *= 1 + 8 * s
        out["packet_loss_pct"] += 4 * s * rng.uniform(0.3, 1, len(df))
        out["throughput_mbps"] *= 1 + 0.6 * s
        out["cpu_util"] += 20 * s
    elif kind == "link_degradation":
        out["crc_errors"] += rng.poisson(400 * s)
        out["packet_loss_pct"] += 3 * s
        out["throughput_mbps"] *= 1 - 0.5 * s
    elif kind == "control_plane_instability":
        out["lsp_flaps"] += rng.poisson(8 * s)
        out["bgp_flaps"] += rng.poisson(4 * s)
        out["cpu_util"] += 25 * s
        out["latency_ms"] *= 1 + 2 * s
    elif kind == "resource_exhaustion":
        out["cpu_util"] = 70 + 28 * s
        out["mem_util"] = 80 + 18 * s
        out["latency_ms"] *= 1 + 1.5 * s
    out["cpu_util"] = out["cpu_util"].clip(0, 100)
    out["mem_util"] = out["mem_util"].clip(0, 100)
    out["packet_loss_pct"] = out["packet_loss_pct"].clip(0, 100)
    return out


def generate_dataset(n_normal: int = 8000, n_anomalous: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    normal = normal_samples(n_normal, rng, load=1.0)
    normal["label"], normal["anomaly_type"] = 0, "none"
    parts = [normal]
    per_kind = n_anomalous // len(ANOMALY_TYPES)
    for kind in ANOMALY_TYPES:
        base = normal_samples(per_kind, rng)
        anomalous = inject(base, kind, rng, rng.uniform(0.25, 1.0, per_kind))
        anomalous["label"], anomalous["anomaly_type"] = 1, kind
        parts.append(anomalous)
    return pd.concat(parts, ignore_index=True).sample(frac=1, random_state=seed).reset_index(drop=True)


if __name__ == "__main__":
    from pathlib import Path
    out = Path(__file__).resolve().parent / "synthetic_mpls_telemetry.csv"
    generate_dataset().to_csv(out, index=False)
    print(f"Wrote {out}")
