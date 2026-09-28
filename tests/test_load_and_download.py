from pathlib import Path

import pytest

from netsentry.data.download import DataFile, import_from, manual_instructions, sha256_of, verify
from netsentry.data.load import SPLIT_FILES, load_split
from netsentry.data.schema import SchemaError


def _write(path: Path, content: bytes) -> DataFile:
    path.write_bytes(content)
    return DataFile(path.name, "folder", sha256_of(path), len(content))


def test_verify_ok_missing_and_mismatch(tmp_path):
    good = _write(tmp_path / "good.csv", b"a,b\n1,2\n")
    bad = _write(tmp_path / "bad.csv", b"x\n")
    (tmp_path / "bad.csv").write_bytes(b"y\n")  # same size, different content
    missing = DataFile("missing.csv", "folder", "0" * 64, 1)
    status = verify(tmp_path, (good, bad, missing))
    assert status == {"good.csv": "ok", "bad.csv": "checksum mismatch", "missing.csv": "missing"}


def test_import_from_copies_only_expected_files(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.mkdir()
    f = _write(src / "wanted.csv", b"1\n")
    (src / "unrelated.csv").write_bytes(b"2\n")
    assert import_from(src, dst, (f,)) == ["wanted.csv"]
    assert sorted(p.name for p in dst.iterdir()) == ["wanted.csv"]


def test_manual_instructions_name_every_file(tmp_path):
    text = manual_instructions(tmp_path)
    assert "UNSW_NB15_training-set.csv" in text
    assert "UNSW_NB15_testing-set.csv" in text


def test_load_split_roundtrip(tmp_path, flows):
    flows.to_csv(tmp_path / SPLIT_FILES["train"], index=False)
    df = load_split("train", tmp_path)
    assert df.shape == flows.shape
    assert str(df["proto"].dtype).startswith("string")


def test_load_split_strips_category_whitespace(tmp_path, flows):
    flows["attack_cat"] = flows["attack_cat"].astype(object) + " "
    flows.to_csv(tmp_path / SPLIT_FILES["test"], index=False)
    df = load_split("test", tmp_path)
    assert not df["attack_cat"].str.endswith(" ").any()


def test_load_split_validates(tmp_path, flows):
    flows.drop(columns="dur").to_csv(tmp_path / SPLIT_FILES["train"], index=False)
    with pytest.raises(SchemaError):
        load_split("train", tmp_path)


def test_load_split_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="make data"):
        load_split("train", tmp_path)


def test_load_split_rejects_unknown_split(tmp_path):
    with pytest.raises(ValueError):
        load_split("validation", tmp_path)
