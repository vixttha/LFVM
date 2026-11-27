"""Validate archive metadata; not a workbook acceptance test."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
archive = root / "library of free virtual machines spreadsheet template version blanks"
for name in ("README.md", "AGENTS.md", "WORKFLOW.md", "TEMPLATE-LAWS.md"):
    assert (root / name).is_file(), name
for name in ("README.md", "AGENTS.md", "agent.md"):
    assert (archive / name).is_file(), name
index = json.loads((archive / "versions.json").read_text(encoding="utf-8"))
versions = index["versions"]
ids = [v["version"] for v in versions]
assert len(ids) == len(set(ids))
assert set(ids) == {p.name for p in archive.iterdir() if p.is_dir() and re.fullmatch(r"v\d+\.\d+\.\d+\.\d+", p.name)}
assert index["active_version"] is None or index["active_version"] in ids
assert sum(not v["locked"] and v["status"] not in {"rejected", "superseded"} for v in versions) <= 1
for i, v in enumerate(versions):
    assert v["path"] == v["version"]
    assert v["predecessor"] is None if i == 0 else v["predecessor"] in ids[:i]
    d = archive / v["path"]
    m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    assert m["template_version"] == v["version"]
    assert m["predecessor"] == v["predecessor"]
    assert m["status"] == v["status"]
    assert m["owner_locked"] == v["locked"]
    assert m["artifact"] == v["artifact"]
    assert m["research_data_included"] is False
    for name in ("README.md", "PLAN.md", "AUDIT.md", "CHANGES.md", "VALIDATION.md"):
        assert (d / name).is_file(), name
    if m["artifact"] is None:
        assert m["artifact_sha256"] is None
        assert not list(d.glob("*.xlsx"))
        assert not m["owner_locked"]
    else:
        assert Path(m["artifact"]).name == m["artifact"]
        f = d / m["artifact"]
        assert f.suffix == ".xlsx" and f.is_file()
        assert hashlib.sha256(f.read_bytes()).hexdigest() == m["artifact_sha256"]
    if m["owner_locked"]:
        assert m["owner_implementation_approved"]
        assert m["status"] in {"locked", "superseded"}
        assert m["artifact"]
        assert m["audit"]["open"] == 0
        assert m["validation"]["planned"] == m["validation"]["passed"] == m["validation"]["executed"]
print(f"Archive metadata checks passed for {len(versions)} version(s); workbook qualification not performed.")
