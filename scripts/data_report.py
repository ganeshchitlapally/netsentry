"""Dataset statistics and leakage audit.

Writes results/dataset_stats.json and results/leakage_audit.csv. Every dataset number
quoted in the README or docs comes from these files.
"""

from __future__ import annotations

import sys

import pandas as pd

from netsentry.config import REPO_ROOT, RESULTS_DIR, load_config
from netsentry.data.load import load_split
from netsentry.data.schema import CATEGORICAL_COLUMNS, CATEGORY_COLUMN, LABEL_COLUMN
from netsentry.data.split import duplicate_groups, train_val_split
from netsentry.features.leakage import TTL_FEATURES, dropped_columns, separability_report
from netsentry.provenance import provenance, write_json


def class_balance(df: pd.DataFrame) -> dict:
    counts = df[CATEGORY_COLUMN].value_counts()
    n_attack = int(df[LABEL_COLUMN].sum())
    return {
        "rows": len(df),
        "attack_rows": n_attack,
        "normal_rows": len(df) - n_attack,
        "attack_fraction": round(n_attack / len(df), 4),
        "attack_cat_counts": {k: int(v) for k, v in counts.items()},
    }


def duplicate_stats(df: pd.DataFrame) -> dict:
    groups = duplicate_groups(df)
    per_group_labels = df.groupby(groups)[LABEL_COLUMN].nunique()
    per_group_cats = df.groupby(groups)[CATEGORY_COLUMN].nunique()
    return {
        "unique_feature_vectors": int(groups.nunique()),
        "rows_duplicating_an_earlier_row": int(groups.duplicated().sum()),
        "vectors_with_conflicting_label": int((per_group_labels > 1).sum()),
        "vectors_with_conflicting_attack_cat": int((per_group_cats > 1).sum()),
    }


def main() -> int:
    cfg = load_config("data")
    raw_dir = REPO_ROOT / cfg["raw_dir"]
    train_full = load_split("train", raw_dir)
    test = load_split("test", raw_dir)
    train, val = train_val_split(train_full, cfg["validation_fraction"], cfg["seed"])

    # Overlap: test rows whose model inputs exactly match some official-training row.
    both = pd.concat([train_full, test], keys=["train", "test"], names=["split"])
    groups = duplicate_groups(both.reset_index(drop=True))
    groups.index = both.index
    train_groups = set(groups.loc["train"])
    test_in_train = groups.loc["test"].isin(train_groups).to_numpy()

    train_full_groups = duplicate_groups(train_full)
    shared_groups = len(
        set(train_full_groups.loc[train.index]) & set(train_full_groups.loc[val.index])
    )

    audit = separability_report(train)  # training portion only, never val/test
    audit.round(4).to_csv(RESULTS_DIR / "leakage_audit.csv", index=False)

    rule = {}  # the single strongest TTL threshold rule, fit and scored on train only
    for thr in sorted(train["sttl"].unique()):
        acc = float(((train["sttl"] >= thr).astype(int) == train[LABEL_COLUMN]).mean())
        if acc > rule.get("train_accuracy", 0):
            rule = {"rule": f"sttl >= {int(thr)}", "train_accuracy": round(acc, 4)}

    stats = {
        "provenance": provenance("scripts/data_report.py"),
        "config": {"seed": cfg["seed"], "validation_fraction": cfg["validation_fraction"]},
        "official_splits": {"train": class_balance(train_full), "test": class_balance(test)},
        "working_splits": {
            "train": class_balance(train),
            "validation": class_balance(val),
            "duplicate_groups_shared_between_train_and_validation": shared_groups,
        },
        "duplicates": {"train": duplicate_stats(train_full), "test": duplicate_stats(test)},
        "test_rows_with_exact_match_in_train": {
            "rows": int(test_in_train.sum()),
            "fraction": round(float(test_in_train.mean()), 4),
            "by_attack_cat": {
                k: int(v)
                for k, v in test.loc[test_in_train, CATEGORY_COLUMN].value_counts().items()
            },
        },
        "categorical_cardinality": {
            c: {
                "train": int(train_full[c].nunique()),
                "test": int(test[c].nunique()),
                "test_values_unseen_in_train": sorted(set(test[c]) - set(train_full[c])),
            }
            for c in CATEGORICAL_COLUMNS
        },
        "leakage": {
            "always_dropped": dropped_columns("all"),
            "ttl_ablation_features": list(TTL_FEATURES),
            "flagged_single_feature_auc_gt_0.9": audit.loc[audit.flagged, "feature"].tolist(),
            "top5_single_feature_auc": audit.head(5)
            .round(4)
            .set_index("feature")["single_feature_auc"]
            .to_dict(),
            "best_single_sttl_threshold_rule_on_train": rule,
        },
    }
    write_json(RESULTS_DIR / "dataset_stats.json", stats)
    print(f"Wrote {RESULTS_DIR / 'dataset_stats.json'} and {RESULTS_DIR / 'leakage_audit.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
