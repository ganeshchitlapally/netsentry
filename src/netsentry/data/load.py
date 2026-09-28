"""Load the official UNSW-NB15 splits with explicit dtypes and schema validation."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from netsentry.data.schema import CATEGORICAL_COLUMNS, CATEGORY_COLUMN, validate

Split = Literal["train", "test"]

SPLIT_FILES: dict[str, str] = {
    "train": "UNSW_NB15_training-set.csv",
    "test": "UNSW_NB15_testing-set.csv",
}


def load_split(split: Split, raw_dir: Path) -> pd.DataFrame:
    """Read one official split, normalise string columns and validate the schema."""
    if split not in SPLIT_FILES:
        raise ValueError(f"split must be one of {sorted(SPLIT_FILES)}, got {split!r}")
    path = Path(raw_dir) / SPLIT_FILES[split]
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found. Run `make data` first.")
    df = pd.read_csv(path)
    for col in (*CATEGORICAL_COLUMNS, CATEGORY_COLUMN):
        df[col] = df[col].astype("string").str.strip()
    validate(df)
    return df
