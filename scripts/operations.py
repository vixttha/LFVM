"""Read-only evidence checker for the foundation matrix, not release authority.

Call with GitHub API responses and job logs obtained independently of the
candidate. An authenticated transport, actor trust and workbook qualification
are separate; this module cannot grant approval.
"""
from __future__ import annotations
import hashlib
import re

from foundation import CONFIG, exact, require, Invalid

REPO = "vixttha/LFVM"
PYTHONS = ("3.11", "3.14")
PLATFORMS = ("ubuntu-latest", "windows-latest")
REQUIRED_STEPS = (
    "Record runtime",
    "Validate archive and exact CI identity",
    "Normal regression suite",
    "Optimized regression suite",
    "Optimized archive gate",
)
PATHS = {"template_schema":".github/workflows/template-archive.yml",
         "research_data":".github/workflows/library-archive.yml"}
SHA = re.compile(r"[0-9a-f]{40}\Z", re.ASCII)
LOG_LIMIT = 8 * 1024 * 1024

def positive_id(value):
    require(type(value) is int and value > 0, "positive run/job ID required")
    return value

def strip_log_prefix(line):
    # GitHub log timestamps; do not accept arbitrary text before proof markers.
    return re.sub(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z ", "", line).strip()

def verify_job_log(raw, kind, sha, os_name, python_version, minimum_tests):
    require(type(raw) is bytes and 0 < len(raw) <= LOG_LIMIT, "missing or oversized job log")
    require(type(minimum_tests) is int and minimum_tests > 0, "trusted test minimum required")
    lines = [strip_log_prefix(s) for s in raw.decode("utf-8").splitlines()]
    identity = re.compile(r"CI identity: " + re.escape(sha) +
                          r"; event=push; Python=" + re.escape(python_version) +
                          r"\.\d+; platform=" + ("linux" if os_name == "ubuntu-latest" else "win32") + r"\Z")
    require(sum(bool(identity.fullmatch(s)) for s in lines) == 2, "missing exact identity gates")
    gate = f"FOUNDATION METADATA PASS: {kind}; pre-build only; release and workbook qualification disabled"
    require(lines.count(gate) == 2, "missing foundation gate proof")
    require(not any(s.startswith(("FAILED", "OK (", "FOUNDATION REJECTED:")) for s in lines),
            "failed or skipped tests in log")
    counts = [int(m.group(1)) for s in lines if (m := re.fullmatch(r"Ran (\d+) tests? in [0-9.]+s", s))]
    require(len(counts) == 2 and counts[0] == counts[1] and counts[0] >= minimum_tests,
            "incomplete or inconsistent regression counts")
    require(lines.count("OK") == 2, "both Python modes must pass without skips")
    return {"test_count_per_mode": counts[0], "log_sha256": hashlib.sha256(raw).hexdigest()}

def verify_foundation_run(*, kind, sha, run, jobs, log_lookup, minimum_tests):
    """Validate a complete exact-push run retrieved from a trusted GitHub read path.

    The caller pins kind, SHA and minimum test count outside the candidate and
    supplies raw logs for the same run attempt. This does not establish that
    candidate-authored test code is independently trustworthy.
    """
    require(kind in CONFIG and type(sha) is str and SHA.fullmatch(sha), "invalid trusted target")
    require(type(run) is dict and type(jobs) is list, "invalid run/job response")
    rid = positive_id(run.get("id"))
    attempt = positive_id(run.get("run_attempt"))
    for field, expected in (("path", PATHS[kind]), ("head_branch", CONFIG[kind][0]),
                            ("head_sha", sha), ("event", "push"), ("status", "completed"),
                            ("conclusion", "success")):
        exact(run.get(field), expected, "run " + field)
    for field in ("repository", "head_repository"):
        require(type(run.get(field)) is dict, "missing repository identity")
        exact(run[field].get("full_name"), REPO, field)
    matrix = {f"foundation ({o}, {p})": (o,p) for o in PLATFORMS for p in PYTHONS}
    require(len(jobs) == len(matrix), "incomplete or unexpected matrix")
    seen, job_ids, results = set(), set(), []
    for job in jobs:
        require(type(job) is dict, "invalid job response")
        jid = positive_id(job.get("id"))
        name = job.get("name")
        require(type(name) is str and name in matrix and name not in seen and jid not in job_ids,
                "unexpected or duplicate matrix job")
        exact(job.get("run_id"), rid, "job run")
        exact(job.get("run_attempt"), attempt, "job attempt")
        exact(job.get("head_sha"), sha, "job commit")
        exact(job.get("status"), "completed", "job status")
        exact(job.get("conclusion"), "success", "job conclusion")
        os_name, python_version = matrix[name]
        labels = job.get("labels")
        require(type(labels) is list and labels == [os_name], "unexpected runner labels")
        steps = job.get("steps")
        require(type(steps) is list and all(type(s) is dict for s in steps), "missing steps")
        for name_step in REQUIRED_STEPS:
            matches = [s for s in steps if s.get("name") == name_step]
            require(len(matches) == 1, "missing or duplicate required step")
            exact(matches[0].get("status"), "completed", "step status")
            exact(matches[0].get("conclusion"), "success", "step result")
        proof = verify_job_log(log_lookup(rid, attempt, jid), kind, sha, os_name, python_version, minimum_tests)
        results.append({"job_id":jid, "os":os_name, "python":python_version, **proof})
        seen.add(name)
        job_ids.add(jid)
    require(seen == set(matrix), "matrix coverage incomplete")
    return {"receipt_kind":"foundation_metadata", "repository":REPO, "branch":CONFIG[kind][0],
            "commit_sha":sha, "run_id":rid, "run_attempt":attempt,
            "jobs":sorted(results,key=lambda x:(x["os"],x["python"])),
            "workbook_qualified":False, "owner_approved":False}
