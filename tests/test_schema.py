import pandas as pd
import pytest

from netsentry.data.schema import EXPECTED_COLUMNS, SchemaError, validate


def test_valid_frame_passes(flows):
    validate(flows)


def test_schema_has_45_columns():
    assert len(EXPECTED_COLUMNS) == 45
    assert len(set(EXPECTED_COLUMNS)) == 45


def test_missing_column_reported(flows):
    with pytest.raises(SchemaError, match=r"missing columns.*sbytes"):
        validate(flows.drop(columns="sbytes"))


def test_extra_column_reported(flows):
    with pytest.raises(SchemaError, match=r"unexpected columns.*srcip"):
        validate(flows.assign(srcip="10.0.0.1"))


def test_nulls_reported(flows):
    flows.loc[3, "dur"] = None
    with pytest.raises(SchemaError, match="null values"):
        validate(flows)


def test_non_numeric_reported(flows):
    flows["sbytes"] = flows["sbytes"].astype(str)
    with pytest.raises(SchemaError, match=r"non-numeric.*sbytes"):
        validate(flows)


def test_bad_label_reported(flows):
    flows.loc[0, "label"] = 2
    with pytest.raises(SchemaError, match="label values outside"):
        validate(flows)


def test_unknown_attack_category_reported(flows):
    flows["attack_cat"] = flows["attack_cat"].astype(object)
    flows.loc[0, "attack_cat"] = "Ransomware"
    with pytest.raises(SchemaError, match=r"unknown attack_cat.*Ransomware"):
        validate(flows)


def test_label_category_disagreement_reported(flows):
    normal_idx = flows.index[flows["attack_cat"] == "Normal"][0]
    flows.loc[normal_idx, "label"] = 1
    with pytest.raises(SchemaError, match="1 rows where label disagrees"):
        validate(flows)


def test_all_problems_reported_together(flows):
    flows.loc[0, "label"] = 5
    flows.loc[1, "dur"] = None
    with pytest.raises(SchemaError) as exc:
        validate(flows)
    assert len(exc.value.problems) >= 2


def test_duplicate_ids_reported(flows):
    flows = pd.concat([flows, flows.head(1)], ignore_index=True)
    with pytest.raises(SchemaError, match="id column is not unique"):
        validate(flows)
