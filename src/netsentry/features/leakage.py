"""Leakage audit: which columns are dropped before modelling, and why.

Two kinds of problem columns:

* Always dropped: ``id`` is a row counter that encodes file position rather than
  flow behaviour (its single-feature AUC in the audit shows how much label signal
  that position carries), and ``label`` / ``attack_cat`` are the targets.
* Ablated, not silently dropped: the TTL features (``sttl``, ``dttl``,
  ``ct_state_ttl``). In the UNSW-NB15 testbed, attack and normal traffic came from
  hosts with different TTL settings, so these features separate the classes very well
  for reasons that would not hold on a real network. Models are reported with and
  without them.

``separability_report`` measures this on the training data instead of just asserting it.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd
from sklearn.metrics import roc_auc_score

from netsentry.data.schema import (
    CATEGORICAL_COLUMNS,
    CATEGORY_COLUMN,
    ID_COLUMN,
    LABEL_COLUMN,
    NUMERIC_COLUMNS,
)

FeatureSet = Literal["all", "no_ttl"]

ALWAYS_DROPPED: dict[str, str] = {
    ID_COLUMN: "row counter; encodes file position, not flow behaviour",
    LABEL_COLUMN: "binary target",
    CATEGORY_COLUMN: "multiclass target (label is derived from it)",
}

TTL_FEATURES: tuple[str, ...] = ("sttl", "dttl", "ct_state_ttl")
TTL_REASON = (
    "testbed artifact: attack and normal hosts used different IP TTLs, so these separate "
    "the classes for reasons that do not transfer to real networks"
)


def feature_columns(feature_set: FeatureSet = "all") -> tuple[list[str], list[str]]:
    """Return (numeric, categorical) model input columns for a feature set."""
    if feature_set not in ("all", "no_ttl"):
        raise ValueError(f"unknown feature_set {feature_set!r}")
    numeric = [c for c in NUMERIC_COLUMNS if not (feature_set == "no_ttl" and c in TTL_FEATURES)]
    return numeric, list(CATEGORICAL_COLUMNS)


def dropped_columns(feature_set: FeatureSet = "all") -> dict[str, str]:
    """Columns excluded from model inputs for this feature set, with the reason for each."""
    dropped = dict(ALWAYS_DROPPED)
    if feature_set == "no_ttl":
        dropped.update(dict.fromkeys(TTL_FEATURES, TTL_REASON))
    return dropped


def separability_report(train: pd.DataFrame, flag_above: float = 0.9) -> pd.DataFrame:
    """Single-feature ROC-AUC against ``label`` for every numeric column (training data only).

    AUC is direction-free (max(auc, 1 - auc)), so 0.5 = useless and 1.0 = perfectly
    separates normal from attack on its own. Features above ``flag_above`` are flagged
    for review; a flag is a prompt to investigate, not an automatic drop.
    """
    rows = []
    y = train[LABEL_COLUMN]
    for col in (ID_COLUMN, *NUMERIC_COLUMNS):  # id included to measure its leakage
        auc = roc_auc_score(y, train[col])
        rows.append({"feature": col, "single_feature_auc": max(auc, 1 - auc)})
    report = pd.DataFrame(rows).sort_values("single_feature_auc", ascending=False)
    report["flagged"] = report["single_feature_auc"] > flag_above
    report["ttl_feature"] = report["feature"].isin(TTL_FEATURES)
    return report.reset_index(drop=True)
