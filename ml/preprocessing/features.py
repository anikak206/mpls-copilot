"""Feature contract shared by training, inference, the API and the database (telemetry columns)."""
import numpy as np

FEATURES = ["cpu_util", "mem_util", "latency_ms", "jitter_ms", "packet_loss_pct",
            "throughput_mbps", "crc_errors", "lsp_flaps", "bgp_flaps"]

# Valid physical ranges (also enforced by DB CHECK constraints and Pydantic validation).
RANGES = {
    "cpu_util": (0, 100), "mem_util": (0, 100), "latency_ms": (0, 10000), "jitter_ms": (0, 5000),
    "packet_loss_pct": (0, 100), "throughput_mbps": (0, 400000), "crc_errors": (0, 10_000_000),
    "lsp_flaps": (0, 100000), "bgp_flaps": (0, 100000),
}

# Heavy-tailed counters/latency are log-transformed before scaling.
LOG_FEATURES = ["latency_ms", "jitter_ms", "packet_loss_pct", "crc_errors", "lsp_flaps", "bgp_flaps"]

LABELS = {
    "cpu_util": "CPU utilisation", "mem_util": "Memory utilisation", "latency_ms": "LSP latency",
    "jitter_ms": "Jitter", "packet_loss_pct": "Packet loss", "throughput_mbps": "Throughput",
    "crc_errors": "Interface CRC errors", "lsp_flaps": "LSP flaps", "bgp_flaps": "BGP session flaps",
}


class FeatureValidationError(ValueError):
    pass


def validate_features(values: dict) -> np.ndarray:
    """Feature-consistency check: all features present, numeric, finite and in range."""
    missing = [f for f in FEATURES if f not in values or values[f] is None]
    if missing:
        raise FeatureValidationError(f"Missing features: {', '.join(missing)}")
    row = []
    for name in FEATURES:
        try:
            value = float(values[name])
        except (TypeError, ValueError):
            raise FeatureValidationError(f"{name} must be numeric")
        low, high = RANGES[name]
        if not np.isfinite(value) or value < low or value > high:
            raise FeatureValidationError(f"{name}={value} outside valid range [{low}, {high}]")
        row.append(value)
    return np.array([row], dtype=float)


def check_frame(df):
    """Dataset-level consistency check used before training/evaluation."""
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        raise FeatureValidationError(f"Dataset missing columns: {missing}")
    if df[FEATURES].isna().any().any():
        raise FeatureValidationError("Dataset contains NaN values")
    for name, (low, high) in RANGES.items():
        if (df[name] < low).any() or (df[name] > high).any():
            raise FeatureValidationError(f"Dataset column {name} out of range")
    return df
