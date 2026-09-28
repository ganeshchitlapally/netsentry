"""Shared fixtures. All data here is synthetic; the real dataset is never needed for tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from netsentry.data.schema import (
    ATTACK_CATEGORIES,
    CATEGORY_COLUMN,
    EXPECTED_COLUMNS,
    ID_COLUMN,
    LABEL_COLUMN,
    NUMERIC_COLUMNS,
)


def make_flows(n: int = 400, seed: int = 0, n_duplicates: int = 40) -> pd.DataFrame:
    """Random rows with the UNSW-NB15 schema; every category appears; includes exact duplicates."""
    rng = np.random.default_rng(seed)
    cats = np.array(ATTACK_CATEGORIES)[np.arange(n) % len(ATTACK_CATEGORIES)]
    df = pd.DataFrame({c: rng.integers(0, 1000, n).astype(float) for c in NUMERIC_COLUMNS}).assign(
        proto=rng.choice(["tcp", "udp", "arp", "ospf"], n, p=[0.6, 0.3, 0.07, 0.03]),
        service=rng.choice(["-", "http", "dns"], n),
        state=rng.choice(["FIN", "INT", "CON"], n),
        attack_cat=cats,
    )
    df[LABEL_COLUMN] = (df[CATEGORY_COLUMN] != "Normal").astype(int)
    df.iloc[n - n_duplicates :, :-1] = df.iloc[:n_duplicates, :-1].to_numpy()  # dup rows
    df[LABEL_COLUMN] = (df[CATEGORY_COLUMN] != "Normal").astype(int)
    df[ID_COLUMN] = np.arange(1, n + 1)
    for c in ("proto", "service", "state", CATEGORY_COLUMN):
        df[c] = df[c].astype("string")
    return df[list(EXPECTED_COLUMNS)]


@pytest.fixture
def flows() -> pd.DataFrame:
    return make_flows()
