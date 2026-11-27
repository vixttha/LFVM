"""Verify the historical installation receipt and targeted LFVM documentation repairs."""
import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)

def check_target(source, raw, root=ROOT):
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc:
        return
    target = (source.parent / unquote(parsed.path)).resolve() if parsed.path else source.resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError(f"missing or unsafe local target: {source.name}: {raw}")
    if parsed.fragment and target.suffix == ".md":
        slug = unquote(parsed.fragment)
        if not any(re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") == slug
                   for h in re.findall(r"(?m)^#{1,6} +(.+?)\s*$", target.read_text(encoding="utf-8"))):
            raise ValueError(f"missing heading: {raw}")

def main():
    repair = json.loads((ROOT / "LFVM-REPAIR.json").read_text())
    base = repair["base_commit"]
    historical = git("show", base + ":LFVM-INSTALL.json")
    assert (ROOT / "LFVM-INSTALL.json").read_bytes() == historical, "historical receipt changed"
    install = json.loads(historical)
    assert install["repository"] == "vixttha/LFVM"
    assert install["branch"] == repair["branch"]
    for path, digest in install["files_sha256"].items():
        assert hashlib.sha256(git("show", base + ":" + path)).hexdigest() == digest, path
    print("PASS: historical receipt and pinned original file digests")
    for link in repair["links"]:
        source = ROOT / link["source"]
        assert "(" + link["target"] + ")" in source.read_text(encoding="utf-8"), link
        check_target(source, link["target"])
        print("PASS:", link["source"], "->", link["target"])
    for path in repair["added_paths"]:
        assert (ROOT / path).is_file(), path
    for invalid in ["__lfvm_missing_target__.md", "../../__lfvm_outside__.md"]:
        try:
            check_target(ROOT / "LFVM-CONTEXT.md", invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid link accepted")
    print("PASS: negative link controls")
    print("Checkout:", git("rev-parse", "HEAD").decode().strip())

if __name__ == "__main__":
    main()
