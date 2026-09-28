import pytest

from netsentry.data.split import duplicate_groups, train_val_split


def test_duplicate_groups_identify_identical_rows(flows):
    groups = duplicate_groups(flows)
    # conftest copies the first 40 rows' features onto the last 40
    assert (groups.iloc[:40].to_numpy() == groups.iloc[-40:].to_numpy()).all()
    assert groups.nunique() == len(flows) - 40


def test_duplicate_groups_ignore_id_and_targets(flows):
    changed = flows.copy()
    changed["id"] = changed["id"] + 10_000
    assert (duplicate_groups(changed) == duplicate_groups(flows)).all()


def test_split_partitions_rows(flows):
    train, val = train_val_split(flows, 0.2, seed=1)
    assert len(train) + len(val) == len(flows)
    assert set(train.index).isdisjoint(val.index)


def test_split_keeps_duplicates_on_one_side(flows):
    train, val = train_val_split(flows, 0.2, seed=1)
    groups = duplicate_groups(flows)
    assert set(groups.loc[train.index]).isdisjoint(groups.loc[val.index])


def test_split_is_deterministic_and_seed_dependent(flows):
    a, _ = train_val_split(flows, 0.2, seed=1)
    b, _ = train_val_split(flows, 0.2, seed=1)
    c, _ = train_val_split(flows, 0.2, seed=2)
    assert a.index.equals(b.index)
    assert not a.index.equals(c.index)


def test_split_is_roughly_stratified(flows):
    _, val = train_val_split(flows, 0.2, seed=1)
    assert set(val["attack_cat"]) == set(flows["attack_cat"])
    assert 0.1 < len(val) / len(flows) < 0.3


@pytest.mark.parametrize("bad", [0, 0.5, 1.2])
def test_split_rejects_bad_fraction(flows, bad):
    with pytest.raises(ValueError):
        train_val_split(flows, bad, seed=1)
