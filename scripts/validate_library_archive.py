"""Metadata and artifact inventory checks only; no provider or workbook qualification."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
archive = root / "library of free virtual machines spreadsheet version filled"
states = {"blocked_on_template", "planned", "approved", "implementing", "validating", "review_pending", "qualified", "locked", "superseded", "rejected"}
hex64 = lambda s: isinstance(s, str) and re.fullmatch(r"[0-9a-f]{64}", s)
for name in ("README.md", "AGENTS.md", "WORKFLOW.md", "LIBRARY-LAWS.md", "TEMPLATE-CONTRACT.md"):
    assert (root / name).is_file(), name
for name in ("README.md", "AGENTS.md", "agent.md"):
    assert (archive / name).is_file(), name
index = json.loads((archive / "versions.json").read_text(encoding="utf-8"))
assert index["version_kind"] == "research_data"
assert index["branch"] == "library-of-free-virtual-machines-spreadsheet-library"
versions = index["versions"]
ids = [r["version"] for r in versions]
assert len(ids) == len(set(ids))
assert set(ids) == {p.name for p in archive.iterdir() if p.is_dir() and re.fullmatch(r"v\d+\.\d+\.\d+\.\d+", p.name)}
active = [r["version"] for r in versions if r["status"] not in {"locked", "superseded", "rejected"}]
assert active == ([] if index["active_version"] is None else [index["active_version"]])
for i, r in enumerate(versions):
    assert r["status"] in states
    assert r["path"] == r["version"]
    assert r["predecessor"] is None if i == 0 else r["predecessor"] in ids[:i]
    d = archive / r["path"]
    m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    for mk, rk in (("data_version", "version"), ("predecessor", "predecessor"), ("status", "status"), ("owner_locked", "locked"), ("artifacts", "artifacts")):
        assert m[mk] == r[rk], (d, mk)
    for name in ("README.md", "PLAN.md", "AUDIT.md", "CHANGES.md", "VALIDATION.md", "RECONCILIATION.md"):
        assert (d / name).is_file(), name
    t = m["template"]
    assert t["branch"] == "library-of-free-virtual-machines-spreadsheet-template"
    paths = []
    for a in m["artifacts"]:
        p = Path(a["path"])
        assert not p.is_absolute() and ".." not in p.parts and str(p) != "."
        f = d / p
        assert f.is_file() and f.resolve().is_relative_to(d.resolve())
        assert hex64(a["sha256"])
        assert hashlib.sha256(f.read_bytes()).hexdigest() == a["sha256"]
        paths.append(p.as_posix())
    assert len(paths) == len(set(paths))
    assert {p.relative_to(d).as_posix() for p in d.rglob("*.xlsx")} == {p for p in paths if p.endswith(".xlsx")}
    s = m["source_baseline"]
    val = m["validation"]
    assert 0 <= val["passed"] <= val["executed"] <= val["planned"]
    assert 0 <= s["imported_source_records"] <= s["expected_source_records"]
    if r["status"] == "blocked_on_template":
        assert t["accepted_version"] is None and t["commit_sha"] is None and t["sha256"] is None
        assert not m["owner_import_approved"] and not r["locked"]
        assert not paths and s["imported_source_records"] == 0 and val["executed"] == 0
    if paths or r["status"] in {"implementing", "validating", "review_pending", "qualified", "locked", "superseded"}:
        assert m["owner_import_approved"]
        assert t["accepted_version"] and t["artifact_path"] and hex64(t["sha256"])
        assert isinstance(t["commit_sha"], str) and re.fullmatch(r"[0-9a-f]{40}", t["commit_sha"])
    if r["locked"]:
        assert r["status"] in {"locked", "superseded"}
        assert any(p.endswith(".xlsx") for p in paths)
        assert s["imported_source_records"] == s["expected_source_records"]
        assert hex64(s["source_snapshot_sha256"])
        assert val["passed"] == val["executed"] == val["planned"]
    if r["status"] in {"locked", "superseded"}:
        assert r["locked"]
print(f"Filled archive metadata checks passed for {len(versions)} version(s); data qualification not performed.")
