"""Independent-verifier primitives. Never trust candidate-supplied keys or run lookups.

The active archive gate remains pre-build only. These functions are exercised with
synthetic fixtures, not production authorizations or accepted workbooks.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import hashlib
import ipaddress
from itertools import islice
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unicodedata
from urllib.parse import parse_qsl, unquote, urlsplit

from foundation import (BASE, BASE_DOCS, CONFIG, Invalid, exact, flag, integer, keys,
                        portable_name, preflight_xlsx, regular, require,
                        streaming_sha256, strict_json, version)

REPO = "vixttha/LFVM"
NAMESPACE = "lfvm-qualification-v1"
HASH = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
COMMIT = re.compile(r"[0-9a-f]{40}\Z", re.ASCII)
RECORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z", re.ASCII)
CONTEXT_FIELDS = ("repository","branch","version_kind","version","scope_sha256","schema_sha256","prior_acceptance_sha256","template")
DEPENDENCY_FIELDS = ("version","commit_sha","schema_sha256","acceptance_sha256","artifact_path","artifact_sha256")
SUITES = {"template_schema":"template_workbook", "research_data":"research_workbook"}


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",",":")).encode("utf-8")


def digest(data):
    require(type(data) is bytes, "digest input must be bytes")
    return hashlib.sha256(data).hexdigest()


def object_digest(obj):
    return digest(canonical(obj))


def hash_value(value, where):
    require(type(value) is str and HASH.fullmatch(value) is not None, f"{where}: invalid digest")
    return value


def commit_value(value):
    require(type(value) is str and COMMIT.fullmatch(value) is not None, "invalid commit")
    return value


def record_id(value):
    require(type(value) is str and RECORD.fullmatch(value) is not None, "invalid record ID")
    return value


def path_parts(value):
    require(type(value) is str and 0 < len(value) <= 1024, "invalid relative path")
    require(value == unicodedata.normalize("NFC",value), "noncanonical Unicode path")
    result = value.split("/")
    require(len(result) <= 32, "path depth limit")
    for p in result:
        portable_name(p)
        require(not any(unicodedata.category(c).startswith("C") for c in p), "unsafe Unicode path")
    return result


def safe_file(root, name):
    regular(root, True)
    parts = path_parts(name)
    path = root
    for i,p in enumerate(parts):
        path = path / p
        regular(path, directory=i < len(parts)-1)
    return path


def public_key(value):
    """Only Ed25519 public keys. Reject option injection and noncanonical encodings."""
    require(type(value) is str and len(value) <= 200, "invalid trusted public key")
    parts = value.split(" ")
    require(len(parts) == 2 and parts[0] == "ssh-ed25519", "trusted Ed25519 key required")
    try:
        raw = base64.b64decode(parts[1], validate=True)
    except (binascii.Error, ValueError) as e:
        raise Invalid("invalid trusted public key encoding") from e
    require(len(raw) == 51 and raw.startswith(b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20"), "invalid Ed25519 public key blob")
    require(base64.b64encode(raw).decode("ascii") == parts[1], "noncanonical public key")
    return value


def verify_signature(envelope, expected_payload, trusted_key, role, ssh_keygen="ssh-keygen"):
    """Verify a canonical payload using a public key supplied by a trusted caller."""
    keys(envelope, ("payload","signature"), "signed receipt")
    require(canonical(envelope["payload"]) == canonical(expected_payload), "receipt does not bind expected payload")
    require(role in {"owner","auditor"}, "invalid receipt role")
    key = public_key(trusted_key)
    sig = envelope["signature"]
    require(type(sig) is str and 0 < len(sig) <= 8192, "signature size")
    try:
        binary = base64.b64decode(sig, validate=True)
    except (binascii.Error, ValueError) as e:
        raise Invalid("invalid signature encoding") from e
    require(binary.startswith(b"-----BEGIN SSH SIGNATURE-----") and len(binary) <= 4096, "invalid SSH signature")
    with tempfile.TemporaryDirectory() as d:
        allowed = Path(d)/"allowed_signers"
        signature = Path(d)/"receipt.sig"
        allowed.write_bytes(f"lfvm-{role} {key}\n".encode("ascii"))
        signature.write_bytes(binary)
        try:
            result = subprocess.run([ssh_keygen,"-Y","verify","-f",str(allowed),"-I",f"lfvm-{role}","-n",NAMESPACE,"-s",str(signature)], input=canonical(expected_payload), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        except (OSError,subprocess.SubprocessError) as e:
            raise Invalid("signature verifier unavailable") from e
        require(result.returncode == 0, "signature verification failed")
    return object_digest(envelope)


def context_check(ctx, scope_bytes, schema_bytes):
    keys(ctx, CONTEXT_FIELDS, "release context")
    exact(ctx["repository"], REPO, "repository")
    kind = ctx["version_kind"]
    require(type(kind) is str and kind in CONFIG, "invalid version namespace")
    exact(ctx["branch"], CONFIG[kind][0], "release branch")
    version(ctx["version"])
    require(hash_value(ctx["scope_sha256"],"scope") == digest(scope_bytes), "scope bytes mismatch")
    require(hash_value(ctx["schema_sha256"],"schema") == digest(schema_bytes), "schema bytes mismatch")
    if ctx["prior_acceptance_sha256"] is not None:
        hash_value(ctx["prior_acceptance_sha256"],"predecessor acceptance")
    if kind == "template_schema":
        require(ctx["template"] is None, "template cannot depend on itself")
    else:
        keys(ctx["template"], DEPENDENCY_FIELDS, "template dependency")
    return kind


def artifact_inventory(root):
    """Dedicated version directory inventory, including all candidate documents."""
    regular(root, True)
    result = []
    pending = [(root, [])]
    entry_count = 0
    total_bytes = 0
    while pending:
        current, prefix = pending.pop()
        children = list(islice(current.iterdir(),4097))
        require(bool(children), "empty release inventory directory")
        entry_count += len(children)
        require(len(children) <= 4096 and entry_count <= 8192, "directory entry limit")
        require(len({p.name.casefold() for p in children}) == len(children), "case-colliding file names")
        for p in children:
            parts = prefix + [p.name]
            rel = "/".join(parts)
            path_parts(rel)
            if p.is_dir() and not p.is_symlink():
                regular(p, True)
                pending.append((p, parts))
            else:
                st = regular(p)
                require(p.suffix.lower() in {".xlsx",".json",".csv",".md"}, "unapproved release artifact type")
                require(p.suffix == p.suffix.lower(), "noncanonical artifact suffix")
                total_bytes += st.st_size
                require(total_bytes <= 1073741824, "total artifact size limit")
                result.append({"path":rel,"sha256":streaming_sha256(p),"size_bytes":st.st_size})
                require(len(result) <= 4096, "artifact count limit")
    require(sum(x["size_bytes"] for x in result) <= 1073741824, "total artifact size limit")
    return sorted(result, key=lambda x:x["path"])


def validate_report(report, kind, commit, lookup):
    """lookup is a trusted independent adapter to public-runner job/log evidence."""
    require(type(report) is list, "test report must be a list")
    expected = {f"TEST-{n:03d}" for n in range(1, CONFIG[kind][3]+1)}
    seen = set()
    cached = {}
    platforms = {"ubuntu-latest", "windows-latest"}
    require(len(report) == len(expected) * len(platforms), "each platform requires complete test evidence")
    for row in report:
        keys(row, ("test_id","status","run_id","job_id","evidence_sha256"), "test result")
        tid = row["test_id"]
        require(type(tid) is str and tid in expected, "unexpected test ID")
        exact(row["status"], "pass", "test result")
        require(type(row["run_id"]) is int and row["run_id"] > 0 and type(row["job_id"]) is int and row["job_id"] > 0, "invalid run/job ID")
        hash_value(row["evidence_sha256"], "job evidence")
        job = (row["run_id"],row["job_id"])
        if job not in cached:
            cached[job] = lookup(*job)
        trusted = cached[job]
        require(type(trusted) is dict, "missing independent runner evidence")
        keys(trusted, ("repository","branch","commit_sha","event","runner","conclusion","suite","evidence_sha256","test_ids"), "trusted runner evidence")
        exact(trusted["repository"], REPO, "runner repository")
        exact(trusted["branch"], CONFIG[kind][0], "runner branch")
        exact(trusted["commit_sha"], commit, "runner commit")
        exact(trusted["event"], "push", "runner event")
        runner = trusted["runner"]
        require(type(runner) is str and runner in platforms, "standard public runner required")
        require((runner, tid) not in seen, "duplicate test evidence on platform")
        exact(trusted["conclusion"], "success", "runner conclusion")
        exact(trusted["suite"], SUITES[kind], "workbook qualification suite")
        exact(trusted["evidence_sha256"], row["evidence_sha256"], "runner log digest")
        require(type(trusted["test_ids"]) is list and tid in trusted["test_ids"], "test not evidenced in runner log")
        seen.add((runner, tid))
    require(seen == {(platform, tid) for platform in platforms for tid in expected}, "incomplete acceptance test inventory on one or more platforms")
    return object_digest(sorted(report,key=lambda r:(r["test_id"], r["run_id"], r["job_id"])))


@dataclass(frozen=True)
class AcceptedRelease:
    """In-process result of trusted verification; never deserialize from candidate data."""
    kind: str
    branch: str
    version: str
    commit_sha: str
    schema_sha256: str
    prior_acceptance_sha256: str | None
    acceptance_sha256: str
    inventory: tuple


def verify_dependency(binding, verified):
    keys(binding, DEPENDENCY_FIELDS, "dependency")
    require(type(verified) is AcceptedRelease and verified.kind == "template_schema", "independently verified template required")
    for field,expected in (("version",verified.version),("commit_sha",verified.commit_sha),("schema_sha256",verified.schema_sha256),("acceptance_sha256",verified.acceptance_sha256)):
        exact(binding[field], expected, "template "+field)
    path_parts(binding["artifact_path"])
    require(binding["artifact_path"].endswith(".xlsx"), "template artifact must be XLSX")
    hash_value(binding["artifact_sha256"], "template artifact")
    require(any(path == binding["artifact_path"] and sha == binding["artifact_sha256"] for path,sha,_ in verified.inventory), "template artifact not in accepted inventory")
    return True


def payload(kind, context, **fields):
    return {"contract_version":1,"receipt_kind":kind,"context":context,**fields}


def verify_release(*, context, scope_bytes, schema_bytes, candidate_commit, version_root, report, run_lookup, owner_key, auditor_key, scope_receipt, qualification_receipt, acceptance_receipt, accepted_history, verified_template=None, ssh_keygen="ssh-keygen"):
    """Verify approval/qualification/acceptance against independently supplied data.

    The caller MUST retrieve immutable candidate bytes, commit and actual runner
    logs independently, and load trusted keys outside the candidate. Never call
    this with keys, run lookups or AcceptedRelease objects from untrusted data.
    """
    kind = context_check(context,scope_bytes,schema_bytes)
    exact(version_root.name,context["version"],"candidate version directory")
    verify_history(version_root.parent,accepted_history,context)
    require(public_key(owner_key) != public_key(auditor_key), "distinct owner and auditor keys required")
    commit_value(candidate_commit)
    if kind == "research_data":
        verify_dependency(context["template"], verified_template)
        exact(context["schema_sha256"], verified_template.schema_sha256, "accepted template schema parity")
    else:
        require(verified_template is None, "unexpected template dependency")
    scope_hash = verify_signature(scope_receipt,payload("scope_authorization",context),owner_key,"owner",ssh_keygen)
    entries = artifact_inventory(version_root)
    names = {e["path"] for e in entries}
    docs = set(BASE_DOCS) | {"manifest.json"}
    if kind == "research_data":
        docs.add("RECONCILIATION.md")
    require(docs <= names, "missing accepted documents")
    xlsx = [e for e in entries if e["path"].endswith(".xlsx")]
    require(bool(xlsx), "no workbook candidate")
    for e in xlsx:
        require(preflight_xlsx(safe_file(version_root,e["path"])) == e["sha256"], "candidate package digest mismatch")
    binding = {"candidate_commit":candidate_commit,"inventory_sha256":object_digest(entries),"test_report_sha256":validate_report(report,kind,candidate_commit,run_lookup)}
    qhash = verify_signature(qualification_receipt,payload("candidate_workbook_qualification",context,scope_receipt_sha256=scope_hash,binding=binding),auditor_key,"auditor",ssh_keygen)
    ahash = verify_signature(acceptance_receipt,payload("owner_acceptance",context,scope_receipt_sha256=scope_hash,qualification_receipt_sha256=qhash,binding=binding),owner_key,"owner",ssh_keygen)
    return AcceptedRelease(kind,context["branch"],context["version"],candidate_commit,context["schema_sha256"],context["prior_acceptance_sha256"],ahash,tuple((e["path"],e["sha256"],e["size_bytes"]) for e in entries))


def numeric_version(v):
    return tuple(int(n) for n in version(v)[1:].split("."))


def verify_history(archive_root, accepted, candidate_context):
    """accepted is the complete independently verified, append-only acceptance chain."""
    regular(archive_root, True)
    require(type(accepted) in (list,tuple), "trusted history required")
    prior = None
    last = None
    seen = set()
    for entry in accepted:
        require(type(entry) is AcceptedRelease, "unverified historical acceptance")
        exact(entry.kind,candidate_context["version_kind"],"history namespace")
        exact(entry.branch,CONFIG[entry.kind][0],"history branch")
        version(entry.version)
        commit_value(entry.commit_sha)
        hash_value(entry.acceptance_sha256,"historical acceptance")
        hash_value(entry.schema_sha256,"historical schema")
        if last is None:
            exact(entry.version,BASE,"initial historical version")
        require(entry.version not in seen, "duplicate historical version")
        seen.add(entry.version)
        require(last is None or numeric_version(entry.version) > numeric_version(last), "non-increasing version history")
        require(entry.prior_acceptance_sha256 == prior, "broken acceptance chain")
        d = archive_root / entry.version
        current = artifact_inventory(d)
        exact(tuple((x["path"],x["sha256"],x["size_bytes"]) for x in current),entry.inventory,"historical artifact inventory")
        last,prior = entry.version,entry.acceptance_sha256
    require(candidate_context["prior_acceptance_sha256"] == prior, "candidate predecessor not trusted chain tip")
    require(last is None or numeric_version(candidate_context["version"]) > numeric_version(last), "candidate is not a successor")
    if last is None:
        exact(candidate_context["version"],BASE,"initial acceptance version")
    return True


TRANSITIONS = {
    "blocked_on_template":{"planned","rejected"}, "planned":{"audit_pending","approved","rejected"},
    "audit_pending":{"planned","approved","rejected"}, "approved":{"implementing","rejected"},
    "implementing":{"validating","rejected"}, "validating":{"implementing","review_pending","rejected"},
    "review_pending":{"implementing","qualified","rejected"}, "qualified":{"implementing","locked","rejected"},
    "locked":set(), "rejected":set(),
}


def verify_transition(kind, old, new, *, scope_verified=False, template_verified=False, qualification_verified=False, acceptance_verified=False):
    require(kind in CONFIG and old in TRANSITIONS and new in TRANSITIONS[old], "illegal lifecycle transition")
    require(kind == "research_data" or old != "blocked_on_template", "invalid template state")
    if kind == "research_data" and new != "rejected" and new != "blocked_on_template":
        flag(template_verified,True,"verified template dependency")
    if new in {"approved","implementing","validating","review_pending","qualified","locked"}:
        flag(scope_verified,True,"verified scope")
    if new in {"qualified","locked"}:
        flag(qualification_verified,True,"verified qualification")
    if new == "locked":
        flag(acceptance_verified,True,"verified owner acceptance")
    return True


SECRET = re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----|(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|ASIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{20,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})")
SENSITIVE_QUERY = re.compile(r"(?:token|secret|password|credential|signature|api[_-]?key|auth|session)",re.I)


def public_url(value):
    require(type(value) is str and len(value) <= 4096 and not any(ord(c)<32 for c in value), "invalid URL")
    try:
        u = urlsplit(value)
        port = u.port
    except ValueError as exc:
        raise Invalid("invalid public URL") from exc
    require(u.scheme == "https" and u.hostname and u.username is None and u.password is None and port in (None,443) and "\\" not in value and not any(c.isspace() for c in value), "public HTTPS URL required")
    host = u.hostname.rstrip(".").lower()
    require(host not in {"localhost","notion.so","www.notion.so","app.notion.com"} and not host.endswith((".local",".internal",".localhost",".notion.so")), "private/workspace URL")
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        require("." in host and bool(re.fullmatch(r"[a-z0-9.-]+", host)) and bool(re.fullmatch(r"[a-z][a-z0-9-]*",host.rsplit(".",1)[-1])), "nonpublic or ambiguous hostname")
    else:
        require(addr.is_global, "nonpublic IP address")
    decoded = unquote(value)
    require(SECRET.search(decoded) is None and not any(ord(c) < 32 for c in decoded), "sensitive or unsafe URL content")
    require(not any(SENSITIVE_QUERY.search(k) for k,_ in parse_qsl(u.query,keep_blank_values=True)), "sensitive URL parameter")
    require(not SENSITIVE_QUERY.search(unquote(u.fragment)), "sensitive URL fragment")
    return True


def public_text(value):
    require(type(value) is str and len(value) <= 65536 and "\x00" not in value, "invalid public text")
    require(SECRET.search(value) is None, "potential credential in public data")
    for candidate in re.findall(r"https?://[^\s<>\"']+",value):
        public_url(candidate.rstrip(".,);]"))
    return True


def scan_json(value, depth=0):
    require(depth <= 32, "source nesting limit")
    if type(value) is str:
        public_text(value)
    elif type(value) is dict:
        for k,v in value.items():
            public_text(k)
            scan_json(v,depth+1)
    elif type(value) is list:
        for v in value:
            scan_json(v,depth+1)
    else:
        require(value is None or type(value) in (int,float,bool), "unsupported source value")


def reconcile_sources(snapshot_bytes, expected_digest, ledger, known_offer_ids, expected_count=54):
    """Account for every original source ID, not just imported records."""
    require(hash_value(expected_digest,"source snapshot") == digest(snapshot_bytes), "source snapshot digest mismatch")
    snap = strict_json(snapshot_bytes)
    keys(snap, ("schema_version","records"), "source snapshot")
    integer(snap["schema_version"],1,"snapshot schema")
    records = snap["records"]
    require(type(expected_count) is int and expected_count >= 0 and type(records) is list and len(records) == expected_count, "source baseline count mismatch")
    require(type(known_offer_ids) in (set,frozenset), "trusted normalized offer IDs required")
    for v in known_offer_ids:
        record_id(v)
    sources = {}
    for r in records:
        keys(r,("source_id","original"),"source record")
        sid = record_id(r["source_id"])
        require(sid not in sources and type(r["original"]) is dict, "duplicate or invalid original source")
        scan_json(r["original"])
        sources[sid] = object_digest(r["original"])
    counts = {"imported":0,"duplicate":0,"excluded":0,"superseded":0}
    seen = set()
    mapped = set()
    require(type(ledger) is list, "source ledger required")
    for r in ledger:
        keys(r,("source_id","original_sha256","disposition","target_offer_ids","reason"),"source mapping")
        sid = record_id(r["source_id"])
        require(sid in sources and sid not in seen, "missing or duplicate source mapping")
        exact(r["original_sha256"],sources[sid],"original source digest")
        require(r["disposition"] in counts, "unsupported source disposition")
        targets = r["target_offer_ids"]
        require(type(targets) is list and all(type(x) is str and x in known_offer_ids for x in targets) and len(set(targets)) == len(targets), "unknown or duplicate mapped offer")
        require(type(r["reason"]) is str and len(r["reason"].strip())>0, "mapping reason required")
        public_text(r["reason"])
        if r["disposition"] in {"imported","duplicate"}:
            require(bool(targets),"imported/duplicate source must map to offer")
        if r["disposition"] == "excluded":
            require(not targets,"excluded source cannot create offer")
        counts[r["disposition"]] += 1
        seen.add(sid)
        mapped.update(targets)
    require(seen == set(sources), "source reconciliation incomplete")
    require(mapped == known_offer_ids, "normalized offers without source mapping")
    return {**counts,"accounted":len(seen),"normalized_offer_count":len(known_offer_ids)}


def verify_partitions(root, partitions, read_record_ids):
    """read_record_ids is a trusted approved-schema parser, not manifest assertions."""
    require(type(partitions) is list and 0 < len(partitions) <= 4096, "partition inventory count limit")
    seen_paths,seen_ids = set(),set()
    for part in partitions:
        keys(part,("path","sha256","record_count"),"partition")
        p = part["path"]
        path_parts(p)
        require(p.casefold() not in seen_paths,"duplicate partition path")
        seen_paths.add(p.casefold())
        file = safe_file(root,p)
        require(hash_value(part["sha256"],"partition digest") == streaming_sha256(file),"partition digest mismatch")
        count = part["record_count"]
        require(type(count) is int and 0 <= count <= 1048575, "partition row limit")
        records = read_record_ids(file)
        require(not isinstance(records, (str, bytes, dict)), "partition parser must return record IDs, not scalar or mapping")
        ids = list(islice(iter(records),count+1))
        integer(count,len(ids),"partition record count")
        for rid in ids:
            record_id(rid)
            require(rid not in seen_ids,"duplicate global record ID")
            seen_ids.add(rid)
    return len(seen_ids)
