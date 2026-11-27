"""Independent release-verification adapters. Never enables the prebuild gate.

Inputs are retrieved by a trusted caller, using verifier code outside the
candidate checkout. No production keys or source records are provisioned here.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import re
import subprocess

from foundation import ANCHORS, CONFIG, Invalid, exact, require, regular, version
from qualification import (REPO, SUITES, artifact_inventory, commit_value,
                           digest, hash_value, path_parts, public_key)
from operations import strip_log_prefix, positive_id, LOG_LIMIT

def external_policy(raw, trusted_policy_sha, kind):
    from foundation import strict_json
    require(digest(raw)==trusted_policy_sha,"external trust policy pin mismatch")
    p=strict_json(raw)
    require(type(p) is dict and set(p)=={"repository","branch","version_kind","owner_key","auditor_key","trusted_branch_head","workflow_blob_sha","workflow_path","schema_sha256","scope_sha256","prior_acceptance_sha256"},"trust policy fields")
    require(kind in CONFIG,"unknown trust namespace")
    exact(p["repository"],REPO,"policy repository")
    exact(p["branch"],CONFIG[kind][0],"policy branch")
    exact(p["version_kind"],kind,"policy namespace")
    require(public_key(p["owner_key"])!=public_key(p["auditor_key"]),"distinct trusted signers required")
    commit_value(p["trusted_branch_head"]);commit_value(p["workflow_blob_sha"])
    path_parts(p["workflow_path"])
    require(p["workflow_path"]==(".github/workflows/template-workbook.yml" if kind=="template_schema" else ".github/workflows/library-workbook.yml"),"unexpected workbook workflow")
    for k in ("schema_sha256","scope_sha256"):hash_value(p[k],k)
    if p["prior_acceptance_sha256"] is not None:hash_value(p["prior_acceptance_sha256"],"prior acceptance")
    return p

def git_read(root,*args):
    # Only a trusted, independently obtained Git object store may be used.
    # No hooks, checkout, user-supplied Git commands, or candidate execution.
    try:
        return subprocess.run(["git","--no-replace-objects","-C",str(root),*args],check=True,
          stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60).stdout
    except (OSError,subprocess.SubprocessError) as e:
        raise Invalid("independent Git verification failed") from e

def verify_git_inventory(git_root,kind,commit,branch_head,version_name,version_root,*,workflow_path,workflow_blob_sha):
    """Bind exact Git blobs to independently read local release inventory."""
    require(kind in CONFIG,"invalid namespace")
    commit_value(commit);commit_value(branch_head);commit_value(workflow_blob_sha)
    version(version_name);path_parts(workflow_path)
    for sha in (commit,branch_head):
        exact(git_read(git_root,"rev-parse","--verify",sha+"^{commit}").decode("ascii").strip(),sha,"immutable commit")
    git_read(git_root,"merge-base","--is-ancestor",ANCHORS[kind],commit)
    git_read(git_root,"merge-base","--is-ancestor",commit,branch_head)
    exact(git_read(git_root,"rev-parse",commit+":"+workflow_path).decode("ascii").strip(),workflow_blob_sha,"trusted workflow blob")
    prefix=CONFIG[kind][1]+"/"+version_name+"/"
    entries=git_read(git_root,"ls-tree","-r","-z",commit,"--",prefix).decode("utf-8").split("\x00")
    expected={}
    total=0
    for line in filter(None,entries):
        meta,path=line.split("\t",1)
        mode,typ,blob=meta.split()
        require(mode=="100644" and typ=="blob" and path.startswith(prefix),"unsafe Git object in version")
        commit_value(blob)
        relative=path[len(prefix):];path_parts(relative)
        require(relative not in expected,"duplicate Git object")
        size=int(git_read(git_root,"cat-file","-s",blob).decode("ascii").strip())
        total+=size
        require(0<=size<=104857600 and total<=1073741824 and len(expected)<4096,"Git inventory bound")
        data=git_read(git_root,"cat-file","blob",blob)
        require(len(data)==size,"Git blob size changed")
        expected[relative]={"path":relative,"sha256":digest(data),"size_bytes":size}
    require(expected and artifact_inventory(version_root)==sorted(expected.values(),key=lambda e:e["path"]),"candidate bytes do not match immutable Git objects")
    return sorted(expected.values(),key=lambda e:e["path"])

def workbook_job_evidence(*,kind,commit,policy,run,job,raw_log,workflow_blob_sha):
    """Convert independently retrieved GitHub run/job/log evidence.

    The future workbook workflow must emit exactly one authenticated-by-context
    marker for each test ID. A trusted auditor still has to examine test code
    and actual evidence: candidate log statements alone never confer approval.
    """
    require(kind in CONFIG,"invalid suite namespace")
    commit_value(commit)
    exact(workflow_blob_sha,policy["workflow_blob_sha"],"trusted workflow blob")
    exact(policy["branch"],CONFIG[kind][0],"trusted policy branch")
    for k,val in (("path",policy["workflow_path"]),("head_branch",CONFIG[kind][0]),("head_sha",commit),("event","push"),("status","completed"),("conclusion","success")):
        exact(run.get(k),val,"workbook run "+k)
    for k in ("repository","head_repository"):
        require(type(run.get(k)) is dict,"repository metadata absent")
        exact(run[k].get("full_name"),REPO,k)
    rid=positive_id(run.get("id"));attempt=positive_id(run.get("run_attempt"));positive_id(job.get("id"))
    for k,val in (("run_id",rid),("run_attempt",attempt),("head_sha",commit),("status","completed"),("conclusion","success")):
        exact(job.get(k),val,"workbook job "+k)
    labels=job.get("labels")
    require(type(labels) is list and len(labels)==1 and labels[0] in {"ubuntu-latest","windows-latest"},"standard public runner required")
    runner=labels[0]
    exact(job.get("name"),"workbook ("+runner+")","workbook job name")
    steps=job.get("steps")
    require(type(steps) is list and all(type(s) is dict for s in steps),"workbook step metadata absent")
    for name in ("Verify exact candidate","Workbook acceptance suite"):
        matches=[s for s in steps if s.get("name")==name]
        require(len(matches)==1 and matches[0].get("status")=="completed" and matches[0].get("conclusion")=="success","workbook required step unsuccessful")
    require(type(raw_log) is bytes and 0<len(raw_log)<=LOG_LIMIT,"invalid workbook log")
    lines=[strip_log_prefix(s) for s in raw_log.decode("utf-8").splitlines()]
    identity="LFVM WORKBOOK IDENTITY "+commit+" "+SUITES[kind]+" "+runner
    require(lines.count(identity)==1,"workbook identity missing or repeated")
    expected={f"TEST-{i:03d}" for i in range(1,CONFIG[kind][3]+1)}
    seen=set()
    for line in lines:
        if not line.startswith("LFVM WORKBOOK TEST "):continue
        m=re.fullmatch(r"LFVM WORKBOOK TEST (TEST-[0-9]{3}) PASS",line)
        require(m is not None and m.group(1) in expected and m.group(1) not in seen,"invalid or duplicate workbook test marker")
        seen.add(m.group(1))
    require(seen==expected,"incomplete workbook test markers")
    require(not any(s.startswith(("FOUNDATION METADATA PASS","FAILED","OK (skipped=")) for s in lines),"wrong suite or failed/skipped tests")
    return {"repository":REPO,"branch":CONFIG[kind][0],"commit_sha":commit,"event":"push","runner":runner,
            "conclusion":"success","suite":SUITES[kind],"evidence_sha256":digest(raw_log),"test_ids":sorted(seen)}


def verify_candidate_authority(*, policy_bytes, trusted_policy_sha, git_root, context,
                               scope_bytes, schema_bytes, candidate_commit, version_root,
                               report, get_run, get_job, get_log, scope_receipt,
                               qualification_receipt, acceptance_receipt, accepted_history,
                               verified_template=None):
    """Trusted orchestration adapter; not invoked by the current branch gate.

    The caller must supply a separately pinned policy, independently retrieved
    Git objects and GitHub evidence, and previously verified history/template.
    Real workbook qualification is still a distinct signed acceptance gate.
    """
    from qualification import context_check, verify_release
    kind=context_check(context,scope_bytes,schema_bytes)
    policy=external_policy(policy_bytes,trusted_policy_sha,kind)
    for k in ("scope_sha256","schema_sha256","prior_acceptance_sha256"):
        exact(context[k],policy[k],"externally pinned "+k)
    inventory=verify_git_inventory(git_root,kind,candidate_commit,policy["trusted_branch_head"],
                                  context["version"],version_root,workflow_path=policy["workflow_path"],
                                  workflow_blob_sha=policy["workflow_blob_sha"])
    def lookup(run_id,job_id):
        run=get_run(run_id)
        job=get_job(run_id,run["run_attempt"],job_id)
        exact(run.get("id"),run_id,"requested run")
        exact(job.get("id"),job_id,"requested job")
        return workbook_job_evidence(kind=kind,commit=candidate_commit,policy=policy,
             run=run,job=job,raw_log=get_log(run_id,run["run_attempt"],job_id),
             workflow_blob_sha=policy["workflow_blob_sha"])
    verified=verify_release(context=context,scope_bytes=scope_bytes,schema_bytes=schema_bytes,
         candidate_commit=candidate_commit,version_root=version_root,report=report,run_lookup=lookup,
         owner_key=policy["owner_key"],auditor_key=policy["auditor_key"],scope_receipt=scope_receipt,
         qualification_receipt=qualification_receipt,acceptance_receipt=acceptance_receipt,
         accepted_history=accepted_history,verified_template=verified_template)
    require(tuple((e["path"],e["sha256"],e["size_bytes"]) for e in inventory)==verified.inventory,
            "candidate inventory changed during signed verification")
    require(artifact_inventory(version_root)==inventory,"candidate inventory changed")
    return verified
