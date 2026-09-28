"""Train/validation split carved from the official training set.

Rows with an identical feature vector are kept on the same side of the split
(group-aware), because the training CSV contains many exact duplicates; a random
split would put copies of the same flow in both train and validation and make
validation metrics (and the thresholds tuned on them) optimistic.
"""

from __future__ import annotations

import pandas as pd
from pandas.util import hash_pandas_object
from sklearn.model_selection import StratifiedGroupKFold

from netsentry.data.schema import CATEGORICAL_COLUMNS, CATEGORY_COLUMN, NUMERIC_COLUMNS


def duplicate_groups(df: pd.DataFrame) -> pd.Series:
    """Integer group id per row; rows share an id iff their model inputs are identical."""
    cols = [*NUMERIC_COLUMNS, *CATEGORICAL_COLUMNS]
    row_hash = hash_pandas_object(df[cols], index=False)
    return pd.Series(pd.factorize(row_hash)[0], index=df.index, name="dup_group")


def train_val_split(
    df: pd.DataFrame, val_fraction: float, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Stratified (by attack_cat), duplicate-group-aware split of the official training set."""
    if not 0 < val_fraction < 0.5:
        raise ValueError(f"val_fraction must be in (0, 0.5), got {val_fraction}")
    n_splits = round(1 / val_fraction)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    train_idx, val_idx = next(
        splitter.split(df, y=df[CATEGORY_COLUMN], groups=duplicate_groups(df))
    )
    return df.iloc[train_idx].copy(), df.iloc[val_idx].copy()
