"""Schema of the official UNSW-NB15 training/testing CSVs and validation checks.

Column names and kinds were taken from the official files (45 columns) and the
official feature description file (NUSW-NB15_features.csv).
"""

from __future__ import annotations

import pandas as pd

CATEGORICAL_COLUMNS: tuple[str, ...] = ("proto", "service", "state")

NUMERIC_COLUMNS: tuple[str, ...] = (
    "dur", "spkts", "dpkts", "sbytes", "dbytes", "rate", "sttl", "dttl", "sload", "dload",
    "sloss", "dloss", "sinpkt", "dinpkt", "sjit", "djit", "swin", "stcpb", "dtcpb", "dwin",
    "tcprtt", "synack", "ackdat", "smean", "dmean", "trans_depth", "response_body_len",
    "ct_srv_src", "ct_state_ttl", "ct_dst_ltm", "ct_src_dport_ltm", "ct_dst_sport_ltm",
    "ct_dst_src_ltm", "is_ftp_login", "ct_ftp_cmd", "ct_flw_http_mthd", "ct_src_ltm",
    "ct_srv_dst", "is_sm_ips_ports",
)  # fmt: skip

ID_COLUMN = "id"
LABEL_COLUMN = "label"  # 0 = normal, 1 = attack
CATEGORY_COLUMN = "attack_cat"
NORMAL_CATEGORY = "Normal"

ATTACK_CATEGORIES: tuple[str, ...] = (
    "Normal", "Generic", "Exploits", "Fuzzers", "DoS",
    "Reconnaissance", "Analysis", "Backdoor", "Shellcode", "Worms",
)  # fmt: skip

EXPECTED_COLUMNS: tuple[str, ...] = (
    ID_COLUMN,
    *NUMERIC_COLUMNS,
    *CATEGORICAL_COLUMNS,
    CATEGORY_COLUMN,
    LABEL_COLUMN,
)


class SchemaError(ValueError):
    """Raised when a dataframe does not match the UNSW-NB15 schema."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("Schema validation failed:\n  - " + "\n  - ".join(problems))


def validate(df: pd.DataFrame) -> None:
    """Check columns, dtypes, nulls and labels; raise SchemaError listing every problem."""
    problems: list[str] = []

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    if missing:
        problems.append(f"missing columns: {missing}")
    if extra:
        problems.append(f"unexpected columns: {extra}")
    if missing:
        raise SchemaError(problems)  # later checks assume all columns exist

    non_numeric = [c for c in (ID_COLUMN, *NUMERIC_COLUMNS, LABEL_COLUMN)
                   if not pd.api.types.is_numeric_dtype(df[c])]  # fmt: skip
    if non_numeric:
        problems.append(f"non-numeric dtype in numeric columns: {non_numeric}")

    null_counts = df[list(EXPECTED_COLUMNS)].isna().sum()
    if null_counts.any():
        problems.append(f"null values: {null_counts[null_counts > 0].to_dict()}")

    if not df[ID_COLUMN].is_unique:
        problems.append("id column is not unique")

    bad_labels = set(df[LABEL_COLUMN].dropna().unique()) - {0, 1}
    if bad_labels:
        problems.append(f"label values outside {{0, 1}}: {sorted(bad_labels)}")

    bad_cats = set(df[CATEGORY_COLUMN].dropna().unique()) - set(ATTACK_CATEGORIES)
    if bad_cats:
        problems.append(f"unknown attack_cat values: {sorted(bad_cats)}")

    if not bad_labels and not null_counts.any():
        is_normal = df[CATEGORY_COLUMN] == NORMAL_CATEGORY
        inconsistent = int((is_normal != (df[LABEL_COLUMN] == 0)).sum())
        if inconsistent:
            problems.append(f"{inconsistent} rows where label disagrees with attack_cat")

    if problems:
        raise SchemaError(problems)
