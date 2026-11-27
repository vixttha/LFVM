"""LFVM catalog snapshot controls, not implementation authorization."""
import json
import subprocess
from pathlib import Path
from library import validate

root = Path(__file__).resolve().parents[1]
errors, ideas, features = validate(root)
if errors:
    raise SystemExit("\n".join(errors))
# Preserve the approved initial identifiers as a minimum; allow future additions.
for prefix, count, rows in (("IDEA", 18, ideas), ("FEAT", 40, features)):
    for i in range(1, count + 1):
        ident = f"{prefix}-{i:06d}"
        if ident not in rows:
            raise SystemExit(f"Missing initial catalog ID: {ident}")
for ident, rows, section in (("IDEA-000001", ideas, "ideas"), ("FEAT-000001", features, "features"), ("FEAT-000002", features, "features")):
    prior = json.loads(subprocess.check_output(["git", "show", "a149cef64c89c57cf75e458bde43685d8027db79:" + section + "/records/" + ident + ".json"], cwd=root))
    if rows[ident]["title"] != prior["title"] or rows[ident]["summary"] != prior["summary"]:
        raise SystemExit(f"Original identity changed: {ident}")
for name in ("tools/library.py", "tools/adopter.py", "ideas/schema/v1/idea.schema.json", "features/schema/v1/feature.schema.json", "LFVM-INSTALL.json"):
    prior = subprocess.check_output(["git", "show", "a149cef64c89c57cf75e458bde43685d8027db79:" + name], cwd=root)
    if (root / name).read_bytes() != prior:
        raise SystemExit(f"Original package changed: {name}")
for row in ideas.values():
    for ev in row["evidence"]:
        if ev["repository"] != "vixttha/LFVM":
            raise SystemExit("Unexpected project source")
for row in features.values():
    if row["release_membership"] != "NOT_ASSERTED":
        raise SystemExit("Catalog cannot authorize release")
print(f"PASS: {len(ideas)} ideas, {len(features)} features; initial IDs, package and historical receipt preserved")
