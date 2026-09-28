import json

from netsentry.provenance import provenance, write_json


def test_provenance_fields():
    p = provenance("scripts/example.py")
    assert p["script"] == "scripts/example.py"
    assert set(p) == {"script", "git_commit", "git_dirty", "generated_at_utc", "python"}
    assert p["python"].startswith("3.11")


def test_write_json_creates_parents(tmp_path):
    out = tmp_path / "nested" / "r.json"
    write_json(out, {"a": 1})
    assert json.loads(out.read_text()) == {"a": 1}
    assert out.read_text().endswith("\n")
