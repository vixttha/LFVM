"""Strict LFVM pre-build foundation gate. Not a workbook or release qualification."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import zipfile
from xml.etree import ElementTree as ET

BASE = "v0.0.0.1"
PREFIX = "library-of-free-virtual-machines-spreadsheet-"
CONFIG = {
    "template_schema": (PREFIX + "template", "library of free virtual machines spreadsheet template version blanks", "template_version", 30, {"planned", "audit_pending"}),
    "research_data": (PREFIX + "library", "library of free virtual machines spreadsheet version filled", "data_version", 24, {"blocked_on_template"}),
}
ANCHORS = {
    "template_schema": "b5464dc63d227a44deb797202334078b3488e556",
    "research_data": "b089ded95b378dbc6fbe1f59fe44966b8e2ed1b9",
}
BASE_DOCS = ("README.md", "PLAN.md", "AUDIT.md", "CHANGES.md", "VALIDATION.md")
ROOT_DOCS = ("README.md", "AGENTS.md", "WORKFLOW.md", "FOUNDATION-GATE.md", "ORANGE-TEAM-HANDOFF.md")
SPREADSHEET_SUFFIXES = {".xlsx", ".xls", ".xlsm", ".xlsb", ".xltx", ".xltm", ".xlam", ".ods", ".fods", ".xla", ".xlw", ".sxc", ".numbers"}
VERSION = re.compile(r"v(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){3}\Z", re.ASCII)
HEX64 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
JSON_LIMIT = 262144
DOC_LIMIT = 1048576


class Invalid(ValueError):
    """An explicit validation rejection, including under python -O."""


def require(condition, message):
    if not condition:
        raise Invalid(message)


def keys(obj, expected, where):
    require(type(obj) is dict, f"{where}: expected object")
    require(set(obj) == set(expected), f"{where}: missing or unexpected fields")


def integer(value, expected, where):
    require(type(value) is int and value == expected, f"{where}: expected integer {expected}")


def flag(value, expected, where):
    require(type(value) is bool and value is expected, f"{where}: expected boolean {expected}")


def exact(value, expected, where):
    require(type(value) is type(expected) and value == expected, f"{where}: unexpected value")


def portable_name(name):
    require(type(name) is str and 0 < len(name) <= 240, "invalid path component")
    require(name not in {".", ".."} and not name.endswith((" ", ".")), "unsafe path component")
    require(not any(ord(c) < 32 or c in '<>:"/\\|?*' for c in name), "unsafe path character")
    require(name.split(".")[0].upper() not in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1,10)), *(f"LPT{i}" for i in range(1,10))}, "reserved path component")


def regular(path, directory=False):
    st = path.lstat()
    require(not stat.S_ISLNK(st.st_mode), f"symlink forbidden: {path.name}")
    if hasattr(st, "st_file_attributes"):
        require(not (st.st_file_attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024)), f"reparse point forbidden: {path.name}")
    require(stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode), f"unexpected file type: {path.name}")
    return st


def inventory(path, expected):
    regular(path, True)
    entries = list(path.iterdir())
    names = [p.name for p in entries]
    for p in entries:
        portable_name(p.name)
        regular(p, directory=p.name in expected and expected[p.name] == "dir")
    require(len({n.casefold() for n in names}) == len(names), "case-colliding names")
    require(set(names) == set(expected), f"{path.name}: unexpected or missing archive entries")


def read_bytes(path, limit):
    st = regular(path)
    require(st.st_size <= limit, f"{path.name}: size limit")
    with path.open("rb") as f:
        data = f.read(limit + 1)
    require(len(data) <= limit, f"{path.name}: read limit")
    return data


def document(path):
    text = read_bytes(path, DOC_LIMIT).decode("utf-8")
    require(bool(text.strip()) and "\x00" not in text, f"{path.name}: empty or invalid document")
    return text


def unique_pairs(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, "duplicate JSON key")
        result[k] = v
    return result


def bad_constant(_):
    raise Invalid("non-finite JSON number")


def strict_json(data):
    require(type(data) is bytes and len(data) <= JSON_LIMIT, "JSON size limit")
    return json.loads(data.decode("utf-8"), object_pairs_hook=unique_pairs, parse_constant=bad_constant)


def load(path):
    return strict_json(read_bytes(path, JSON_LIMIT))


def version(value):
    require(type(value) is str and len(value) <= 128 and VERSION.fullmatch(value) is not None, "invalid canonical version")
    return value


def null(value, where):
    require(value is None, f"{where}: must be null in pre-build gate")


def validation(obj, planned):
    keys(obj, ("planned", "executed", "passed"), "validation")
    integer(obj["planned"], planned, "planned test count")
    integer(obj["executed"], 0, "executed workbook tests")
    integer(obj["passed"], 0, "passed workbook tests")


def validate_contract(root):
    c = load(root / "schemas" / "foundation-contract.json")
    keys(c, ("contract_version", "mode", "initial_version", "version_grammar", "branches", "taxonomy", "limits", "receipt_kinds", "release_gate", "publication"), "contract")
    integer(c["contract_version"], 1, "contract version")
    exact(c["mode"], "prebuild_only", "contract mode")
    exact(c["initial_version"], BASE, "initial version")
    keys(c["branches"], CONFIG, "branch contract")
    for kind, (branch, folder, vk, planned, states) in CONFIG.items():
        row = c["branches"][kind]
        common = {"branch", "archive", "allowed_states", "planned_tests", "version_key"}
        keys(row, common | ({"initial_audit_count"} if kind == "template_schema" else {"initial_source_count"}), kind)
        exact(row["branch"], branch, "branch")
        exact(row["archive"], folder, "archive")
        exact(row["version_key"], vk, "version key")
        integer(row["planned_tests"], planned, "planned tests")
        require(type(row["allowed_states"]) is list and set(row["allowed_states"]) == states and len(row["allowed_states"]) == len(states), "state contract mismatch")
        integer(row["initial_audit_count"], 28, "audit count") if kind == "template_schema" else integer(row["initial_source_count"], 54, "source count")
    flag(c["release_gate"]["enabled"], False, "release gate")
    for k in ("free_class", "trust", "access", "billing_risk", "evidence", "compute", "secondary", "value_state", "independent_dimensions"):
        values = c["taxonomy"][k]
        require(type(values) is list and all(type(x) is str and x for x in values) and len(values) == len(set(values)), f"invalid taxonomy: {k}")
    exact(c["taxonomy"]["free_class"], ["F0","F1","F2","F3","F4","F5"], "free classes")
    exact(c["taxonomy"]["trust"], ["A","B","C","U"], "trust grades")
    exact(c["taxonomy"]["access"], ["Public","Approval","Restricted","Closed","Unverified"], "access grades")
    exact(c["taxonomy"]["billing_risk"], ["R0","R1","R2","R3","R4","RU"], "billing risk")
    exact(c["taxonomy"]["evidence"], ["E0","E1","E2","E3","E4","E5","E6"], "evidence")
    return c


def validate(root, kind):
    require(kind in CONFIG, "unknown branch role")
    branch, folder, vk, planned, states = CONFIG[kind]
    regular(root, True)
    for name in ROOT_DOCS + (("TEMPLATE-LAWS.md",) if kind == "template_schema" else ("LIBRARY-LAWS.md", "TEMPLATE-CONTRACT.md")):
        document(root / name)
    regular(root / "schemas", True)
    validate_contract(root)
    archive = root / folder
    inventory(archive, {"README.md":"file", "AGENTS.md":"file", "agent.md":"file", "versions.json":"file", BASE:"dir"})
    for name in ("README.md","AGENTS.md","agent.md"):
        document(archive / name)
    index = load(archive / "versions.json")
    keys(index, ("schema_version", "branch", "version_kind", "active_version", "versions"), "version index")
    integer(index["schema_version"], 1, "index schema version")
    exact(index["branch"], branch, "index branch")
    exact(index["version_kind"], kind, "version namespace")
    exact(index["active_version"], BASE, "active version")
    rows = index["versions"]
    require(type(rows) is list and len(rows) == 1, "initial version required; successor needs accepted release contract")
    r = rows[0]
    field = "artifact" if kind == "template_schema" else "artifacts"
    keys(r, ("version", "path", "predecessor", "status", "locked", field), "index row")
    exact(version(r["version"]), BASE, "index version")
    exact(r["path"], BASE, "version path")
    null(r["predecessor"], "predecessor")
    require(type(r["status"]) is str and r["status"] in states, "state not authorized by pre-build contract")
    flag(r["locked"], False, "index lock")
    if kind == "template_schema":
        null(r[field], "index artifact")
    else:
        exact(r[field], [], "index artifacts")
    docs = BASE_DOCS + (("RECONCILIATION.md",) if kind == "research_data" else ())
    d = archive / BASE
    inventory(d, {name:"file" for name in (*docs, "manifest.json")})
    for name in docs:
        document(d / name)
    m = load(d / "manifest.json")
    common = ("schema_version", vk, "predecessor", "status", "owner_locked", "validation", "documents")
    extra = ("owner_implementation_approved","artifact","artifact_sha256","research_data_included","audit") if kind == "template_schema" else ("owner_import_approved","template","source_baseline","artifacts")
    keys(m, (*common, *extra), "manifest")
    integer(m["schema_version"], 1, "manifest schema version")
    exact(m[vk], BASE, "manifest version")
    null(m["predecessor"], "manifest predecessor")
    exact(m["status"], r["status"], "manifest status")
    flag(m["owner_locked"], False, "manifest lock")
    require(type(m["documents"]) is list and all(type(n) is str for n in m["documents"]) and len(m["documents"]) == len(docs) and set(m["documents"]) == set(docs), "document inventory mismatch")
    validation(m["validation"], planned)
    if kind == "template_schema":
        flag(m["owner_implementation_approved"], False, "implementation approval")
        flag(m["research_data_included"], False, "research data")
        null(m["artifact"], "artifact")
        null(m["artifact_sha256"], "artifact digest")
        a = m["audit"]
        keys(a, ("open", "closed"), "audit")
        require(all(type(a[k]) is int and 0 <= a[k] <= 28 for k in a) and a["open"] + a["closed"] == 28, "audit count mismatch")
    else:
        flag(m["owner_import_approved"], False, "import approval")
        exact(m["artifacts"], [], "artifact inventory")
        t = m["template"]
        keys(t, ("branch","target_version","accepted_version","commit_sha","artifact_path","sha256"), "template dependency")
        exact(t["branch"], CONFIG["template_schema"][0], "template branch")
        exact(version(t["target_version"]), BASE, "target blank version")
        for name in ("accepted_version","commit_sha","artifact_path","sha256"):
            null(t[name], f"template {name}")
        s = m["source_baseline"]
        keys(s, ("expected_source_records","imported_source_records","unique_providers","offer_count","source_snapshot_sha256"), "source baseline")
        integer(s["expected_source_records"], 54, "initial source count")
        integer(s["imported_source_records"], 0, "imported source count")
        for name in ("unique_providers","offer_count","source_snapshot_sha256"):
            null(s[name], name)
    return m


def streaming_sha256(path, limit=104857600):
    require(regular(path).st_size <= limit, "artifact size limit")
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            total += len(part)
            require(total <= limit, "artifact read limit")
            digest.update(part)
    return digest.hexdigest()


def safe_csv_text(value):
    """Preserve data in canonical storage; escape potentially executable CSV text on export."""
    require(type(value) is str, "CSV text must be a string")
    if value.startswith(("\t","\r","\n")) or value.lstrip().startswith(("=","+","-","@","\uff1d","\uff0b","\uff0d","\uff20")):
        return "'" + value
    return value


def preflight_xlsx(path):
    """Conservative package-only check, not accepted-schema or formula qualification."""
    require(path.suffix == ".xlsx", "XLSX suffix required")
    digest = streaming_sha256(path)
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        require(0 < len(infos) <= 4096, "ZIP member count")
        names = set()
        total = 0
        xml = {}
        for i in infos:
            name = i.filename
            require(not i.is_dir() and not name.startswith("/") and "\\" not in name, "unsafe ZIP name")
            for part in name.split("/"):
                portable_name(part)
            require(name.casefold() not in names, "duplicate/colliding ZIP member")
            names.add(name.casefold())
            require(not i.flag_bits & 1 and i.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}, "encrypted/unsupported ZIP member")
            mode = (i.external_attr >> 16) & 0xFFFF
            require(not stat.S_ISLNK(mode), "ZIP symlink")
            require(i.file_size <= 33554432 and i.file_size <= max(i.compress_size, 1)*200, "ZIP member size or ratio")
            total += i.file_size
            require(total <= 268435456, "ZIP expansion limit")
            low = name.casefold()
            require(low.endswith((".xml",".rels")) and not any(x in low for x in ("vbaproject","activex","embeddings/","externallinks/","customui/","connections.xml","querytables/")), "unsupported or active package part")
            with z.open(i) as f:
                data = f.read(33554433)
            require(len(data) == i.file_size and len(data) <= 33554432, "ZIP member length")
            content = data.decode("utf-8-sig")
            require("\x00" not in content and "<!DOCTYPE" not in content.upper() and "<!ENTITY" not in content.upper(), "unsafe XML declaration")
            el = ET.fromstring(content)
            if low.endswith(".rels"):
                for rel in el:
                    require(rel.attrib.get("TargetMode","Internal") == "Internal", "external relationship")
                    target = rel.attrib.get("Target","")
                    require(target and not any(c in target for c in (":","\\","%","?","#")), "unsafe relationship target")
                    # Resolve internal target relative to the owning part, never outside package.
                    stack = [] if name == "_rels/.rels" or target.startswith("/") else name.split("/")[:-2]
                    for component in target.lstrip("/").split("/"):
                        if component == "..":
                            require(bool(stack), "relationship escapes package")
                            stack.pop()
                        elif component != ".":
                            portable_name(component)
                            stack.append(component)
                    require(bool(stack), "empty relationship target")
            if name == "[Content_Types].xml":
                for ct in el:
                    value = ct.attrib.get("ContentType","").lower()
                    require(value and not any(x in value for x in ("macroenabled","vba","activex","oleobject","externalLink".lower())), "active content type")
            xml[name] = el
        require({"[Content_Types].xml","_rels/.rels","xl/workbook.xml"} <= set(xml), "required OOXML parts absent")
        require(xml["xl/workbook.xml"].tag == "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}workbook", "invalid workbook root")
    return digest


def git(root, *args):
    return subprocess.run(["git","-C",str(root),*args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60).stdout


def verify_event(env, kind, actual_sha):
    branch = CONFIG[kind][0]
    require(env.get("GITHUB_REPOSITORY") == "vixttha/LFVM", "unexpected repository")
    require(re.fullmatch(r"[0-9a-f]{40}", actual_sha) is not None and env.get("GITHUB_SHA") == actual_sha, "checkout SHA mismatch")
    event = env.get("GITHUB_EVENT_NAME")
    if event == "push":
        exact(env.get("GITHUB_REF"), "refs/heads/"+branch, "push ref")
    elif event == "pull_request":
        exact(env.get("GITHUB_BASE_REF"), branch, "PR target")
        require(re.fullmatch(r"refs/pull/[1-9][0-9]*/merge", env.get("GITHUB_REF","")) is not None, "PR merge ref required")
    else:
        raise Invalid("unsupported CI event")


def verify_handoff_bytes(original, committed, checkout):
    """Compare immutable Git blobs; tolerate only Git's canonical CRLF checkout transform."""
    require(original == committed, "original handoff Git blob altered")
    require(checkout == committed or (b"\r" not in committed and checkout == committed.replace(b"\n", b"\r\n")), "handoff working tree altered")


def verify_ci(root, kind):
    head = git(root, "rev-parse", "HEAD").decode("ascii").strip()
    verify_event(os.environ, kind, head)
    git(root, "merge-base", "--is-ancestor", ANCHORS[kind], head)
    original = git(root, "show", ANCHORS[kind]+":ORANGE-TEAM-HANDOFF.md")
    committed = git(root, "show", head+":ORANGE-TEAM-HANDOFF.md")
    verify_handoff_bytes(original, committed, read_bytes(root/"ORANGE-TEAM-HANDOFF.md", DOC_LIMIT))
    entries = git(root, "ls-files", "-z", "--stage").decode("utf-8").split("\x00")
    paths = set()
    for row in filter(None, entries):
        meta, path = row.split("\t", 1)
        mode, _, stage = meta.split()
        require(mode in {"100644","100755"} and stage == "0", "tracked symlink, submodule or merge conflict")
        for part in path.split("/"):
            portable_name(part)
        require(path.casefold() not in paths, "case-colliding tracked paths")
        paths.add(path.casefold())
        require(Path(path).suffix.lower() not in SPREADSHEET_SUFFIXES, "spreadsheet artifact forbidden during pre-build")
    print(f"CI identity: {head}; event={os.environ['GITHUB_EVENT_NAME']}; Python={sys.version.split()[0]}; platform={sys.platform}")


def main(kind):
    root = Path(__file__).resolve().parents[1]
    try:
        require(sys.version_info >= (3, 11), "Python 3.11+ required")
        require(sys.argv[1:] in ([], ["--ci"]), "unsupported arguments")
        validate(root, kind)
        if sys.argv[1:] == ["--ci"]:
            verify_ci(root, kind)
    except (ValueError, OSError, TypeError, KeyError, RecursionError, subprocess.SubprocessError) as exc:
        print(f"FOUNDATION REJECTED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"FOUNDATION METADATA PASS: {kind}; pre-build only; release and workbook qualification disabled")
    return 0
