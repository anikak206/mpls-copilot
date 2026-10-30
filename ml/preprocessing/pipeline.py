"""Preprocessing pipeline: log1p on heavy-tailed features, then standard scaling."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from ml.preprocessing.features import FEATURES, LOG_FEATURES

LOG_IDX = [FEATURES.index(f) for f in LOG_FEATURES]
LIN_IDX = [i for i in range(len(FEATURES)) if i not in LOG_IDX]


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("log", Pipeline([("log1p", FunctionTransformer(np.log1p)), ("scale", StandardScaler())]), LOG_IDX),
        ("lin", StandardScaler(), LIN_IDX),
    ])


def transformed_feature_order():
    """Feature names in the column order produced by build_preprocessor()."""
    return [FEATURES[i] for i in LOG_IDX] + [FEATURES[i] for i in LIN_IDX]
