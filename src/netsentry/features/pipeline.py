"""Preprocessing pipeline. Always fit on training data only, then applied unchanged to val/test."""

from __future__ import annotations

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from netsentry.features.leakage import FeatureSet, feature_columns


def signed_log1p(x):
    """log1p that is defined for negative values; tames the heavy tails of byte/packet counts."""
    return np.sign(x) * np.log1p(np.abs(x))


def build_preprocessor(
    feature_set: FeatureSet = "all", min_category_frequency: int = 20
) -> ColumnTransformer:
    """Numeric: signed log1p then standardise. Categorical: one-hot.

    Categories seen fewer than ``min_category_frequency`` times in training are pooled
    into one "infrequent" column (``proto`` has over a hundred mostly-rare values).
    Categories never seen in training map to that infrequent column when it exists,
    otherwise to all zeros, instead of raising.
    """
    numeric, categorical = feature_columns(feature_set)
    numeric_pipe = Pipeline(
        [
            ("log", FunctionTransformer(signed_log1p, feature_names_out="one-to-one")),
            ("scale", StandardScaler()),
        ]
    )
    categorical_pipe = OneHotEncoder(
        handle_unknown="infrequent_if_exist",
        min_frequency=min_category_frequency,
        sparse_output=False,
        dtype=np.float32,
    )
    return ColumnTransformer(
        [("num", numeric_pipe, numeric), ("cat", categorical_pipe, categorical)],
        remainder="drop",  # ids and targets never reach the model
        verbose_feature_names_out=False,
    )
