from pathlib import Path

import pytest

from netsentry.config import CONFIG_DIR, REPO_ROOT, load_config


def test_repo_root_contains_pyproject():
    assert (REPO_ROOT / "pyproject.toml").is_file()


def test_data_config_has_expected_keys():
    cfg = load_config("data")
    assert isinstance(cfg["seed"], int)
    assert 0 < cfg["validation_fraction"] < 1
    assert CONFIG_DIR.is_dir()


def test_missing_config_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_config("does_not_exist", config_dir=tmp_path)


def test_non_mapping_config_raises(tmp_path: Path):
    (tmp_path / "bad.yaml").write_text("- just\n- a list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_config("bad", config_dir=tmp_path)
