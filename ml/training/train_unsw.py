"""OPTIONAL benchmark pipeline for UNSW-NB15 (not executed in this environment).

UNSW-NB15 is a network-intrusion benchmark, NOT a dataset of MPLS device failures. Download the
official CSVs (UNSW_NB15_training-set.csv / UNSW_NB15_testing-set.csv) from the UNSW Canberra
Cyber Range Lab site and run:
    python -m ml.training.train_unsw --train path/to/training.csv --test path/to/testing.csv
Feature mapping used (approximate, documented limitation):
    sload->throughput, sjit->jitter, synack+ackdat->latency proxy, sloss/spkts->loss %, label->anomaly.
The resulting model is saved separately (unsw_model.joblib) and is NOT used by the application.
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

COLUMNS = ["sload", "dload", "sjit", "djit", "synack", "ackdat", "sloss", "dloss", "spkts", "dpkts", "dur"]
OUT = Path(__file__).resolve().parent.parent / "models"


def load(path):
    df = pd.read_csv(path)
    missing = [c for c in COLUMNS + ["label"] if c not in df.columns]
    if missing:
        raise SystemExit(f"Not a UNSW-NB15 CSV, missing {missing}")
    return np.log1p(df[COLUMNS].clip(lower=0).to_numpy(float)), df["label"].to_numpy(int)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True)
    parser.add_argument("--test", required=True)
    args = parser.parse_args()
    x_train, y_train = load(args.train)
    x_test, y_test = load(args.test)
    model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1).fit(x_train, y_train)
    report = classification_report(y_test, model.predict(x_test), output_dict=True)
    joblib.dump({"model": model, "columns": COLUMNS}, OUT / "unsw_model.joblib")
    (OUT / "unsw_metrics.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
