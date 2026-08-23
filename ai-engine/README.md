# AI Engine (Person 2)

Owns Phases 4-7: data preparation, anomaly detection, failure prediction,
risk/explainability, and recommendation logic.

## Layout
- `data_prep/` — cleaning scripts, feature engineering, train/val/test splits.
  Raw data should NOT be committed (see repo `.gitignore`) — keep it local or
  in a shared drive; commit the scripts that produce it instead.
- `models/` — training scripts, evaluation notebooks/scripts, exported model
  artifacts. Export as ONNX or a pickled sklearn/XGBoost model so the backend
  can load it for offline inference without needing internet access.
- `notebooks/` — exploratory work. Clean these up into scripts in `data_prep/`
  or `models/` before merging into `main`.

## Suggested requirements.txt for this folder
```
pandas
numpy
scikit-learn
xgboost
shap
matplotlib
jupyter
```
(Add a `requirements.txt` here once you start Phase 4 — keep it separate from
`backend/requirements.txt` since the backend shouldn't need training-only
dependencies like `jupyter`.)

## Handoff contract with the backend
Whatever you produce here should be loadable by `backend/app/routers/predictions.py`
without a network call — e.g. a `.pkl`/`.onnx` file the backend loads at startup.
Agree the exact input feature order and output format with Person 1 before Phase 5
ends, so Phase 6 (risk/explainability) doesn't get blocked on a mismatch.
