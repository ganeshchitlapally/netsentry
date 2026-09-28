import numpy as np
import pytest

from netsentry.data.schema import CATEGORY_COLUMN, ID_COLUMN, LABEL_COLUMN
from netsentry.features.leakage import (
    TTL_FEATURES,
    dropped_columns,
    feature_columns,
    separability_report,
)
from netsentry.features.pipeline import build_preprocessor, signed_log1p


def test_targets_and_id_never_model_inputs():
    for fs in ("all", "no_ttl"):
        numeric, categorical = feature_columns(fs)
        inputs = set(numeric) | set(categorical)
        assert inputs.isdisjoint({ID_COLUMN, LABEL_COLUMN, CATEGORY_COLUMN})


def test_no_ttl_feature_set_excludes_ttl():
    all_num, _ = feature_columns("all")
    no_ttl_num, _ = feature_columns("no_ttl")
    assert set(TTL_FEATURES) <= set(all_num)
    assert set(TTL_FEATURES).isdisjoint(no_ttl_num)
    assert set(all_num) - set(no_ttl_num) == set(TTL_FEATURES)


def test_dropped_columns_have_reasons():
    dropped = dropped_columns("no_ttl")
    assert set(dropped) >= {ID_COLUMN, LABEL_COLUMN, CATEGORY_COLUMN, *TTL_FEATURES}
    assert all(reason.strip() for reason in dropped.values())


def test_unknown_feature_set_rejected():
    with pytest.raises(ValueError):
        feature_columns("everything")


def test_separability_flags_a_leaky_feature(flows):
    flows["sttl"] = flows[LABEL_COLUMN] * 200 + 10  # perfectly separating, like the TTL artifact
    report = separability_report(flows)
    top = report.iloc[0]
    assert top["feature"] == "sttl"
    assert top["single_feature_auc"] == pytest.approx(1.0)
    assert bool(top["flagged"]) and bool(top["ttl_feature"])
    assert report["single_feature_auc"].between(0.5, 1.0).all()


def test_signed_log1p_handles_negatives_and_zero():
    x = np.array([-np.e + 1, 0.0, np.e - 1])
    assert np.allclose(signed_log1p(x), [-1.0, 0.0, 1.0])


@pytest.mark.parametrize("feature_set", ["all", "no_ttl"])
def test_preprocessor_output_shape_and_finite(flows, feature_set):
    pre = build_preprocessor(feature_set, min_category_frequency=5)
    out = pre.fit_transform(flows)
    names = pre.get_feature_names_out()
    assert out.shape == (len(flows), len(names))
    assert np.isfinite(out).all()
    assert not any(n in names for n in (ID_COLUMN, LABEL_COLUMN, CATEGORY_COLUMN))
    assert any(n in names for n in TTL_FEATURES) == (feature_set == "all")


def test_preprocessor_uses_training_statistics_only(flows):
    train, test = flows.iloc[:300], flows.iloc[300:].copy()
    test["sbytes"] = test["sbytes"] + 1e6  # shift test distribution
    pre = build_preprocessor(min_category_frequency=5).fit(train)
    scaler = pre.named_transformers_["num"].named_steps["scale"]
    names = list(pre.named_transformers_["num"].get_feature_names_out())
    expected_mean = signed_log1p(train["sbytes"].to_numpy()).mean()
    assert scaler.mean_[names.index("sbytes")] == pytest.approx(expected_mean)
    # a shifted test set is transformed with train stats, so it does NOT come out centred
    col = list(pre.get_feature_names_out()).index("sbytes")
    assert pre.transform(test)[:, col].mean() > 3


def test_preprocessor_handles_unseen_category(flows):
    pre = build_preprocessor(min_category_frequency=5).fit(flows)
    unseen = flows.head(3).copy()
    unseen["state"] = unseen["state"].astype(object)
    unseen.loc[unseen.index, "state"] = "ACC"  # appears only in the official test split
    out = pre.transform(unseen)
    assert np.isfinite(out).all()


def test_rare_categories_pooled(flows):
    pre = build_preprocessor(min_category_frequency=50).fit(flows)
    proto_cols = [n for n in pre.get_feature_names_out() if n.startswith("proto_")]
    assert "proto_infrequent_sklearn" in proto_cols  # arp/ospf are rare in the fixture
