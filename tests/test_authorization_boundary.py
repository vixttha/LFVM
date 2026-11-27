"""Tests for external trust and independently retrieved workbook evidence."""
from pathlib import Path
import base64
import subprocess
from unittest.mock import patch
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from foundation import CONFIG, Invalid
from qualification import canonical, digest, REPO, SUITES
from authorization_boundary import external_policy, workbook_job_evidence, verify_git_inventory
from foundation import ANCHORS
from authorization_boundary import git_read

class BoundaryTests(unittest.TestCase):
    def key(self,fill):
        # Synthetic public-key blobs for format checks only; not signing identities.
        return "ssh-ed25519 "+base64.b64encode(b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20"+fill*32).decode("ascii")
    def fixture(self):
        kind="template_schema";commit="a"*40;runner="ubuntu-latest"
        policy={"repository":REPO,"branch":CONFIG[kind][0],"version_kind":kind,"owner_key":self.key(b"a"),
          "auditor_key":self.key(b"b"),"trusted_branch_head":commit,"workflow_blob_sha":"b"*40,
          "workflow_path":".github/workflows/template-workbook.yml","schema_sha256":"c"*64,"scope_sha256":"d"*64,
          "prior_acceptance_sha256":None}
        run={"id":1,"run_attempt":2,"path":policy["workflow_path"],"head_branch":CONFIG[kind][0],"head_sha":commit,
             "event":"push","status":"completed","conclusion":"success","repository":{"full_name":REPO},"head_repository":{"full_name":REPO}}
        job={"id":3,"run_id":1,"run_attempt":2,"head_sha":commit,"status":"completed","conclusion":"success",
             "labels":[runner],"name":"workbook ("+runner+")","steps":[{"name":n,"status":"completed","conclusion":"success"} for n in ("Verify exact candidate","Workbook acceptance suite")]}
        raw=("\n".join(["LFVM WORKBOOK IDENTITY "+commit+" "+SUITES[kind]+" "+runner]+[f"LFVM WORKBOOK TEST TEST-{i:03d} PASS" for i in range(1,31)])+"\n").encode()
        return dict(kind=kind,commit=commit,policy=policy,run=run,job=job,raw_log=raw,workflow_blob_sha="b"*40)
    def reject(self,edit):
        a=self.fixture();edit(a)
        with self.assertRaises(Invalid):workbook_job_evidence(**a)
    def test_external_policy(self):
        a=self.fixture();raw=canonical(a["policy"])
        self.assertEqual(external_policy(raw,digest(raw),a["kind"]),a["policy"])
    def test_external_pin(self):
        a=self.fixture()
        with self.assertRaises(Invalid):external_policy(canonical(a["policy"]),"0"*64,a["kind"])
    def test_same_signers(self):
        a=self.fixture();a["policy"]["auditor_key"]=a["policy"]["owner_key"];raw=canonical(a["policy"])
        with self.assertRaises(Invalid):external_policy(raw,digest(raw),a["kind"])
    def test_workbook_evidence(self):
        p=workbook_job_evidence(**self.fixture())
        self.assertEqual(len(p["test_ids"]),30);self.assertEqual(p["suite"],"template_workbook")
    def test_workflow_digest(self):self.reject(lambda a:a.update(workflow_blob_sha="0"*40))
    def test_wrong_run(self):self.reject(lambda a:a["run"].update(head_sha="0"*40))
    def test_wrong_attempt(self):self.reject(lambda a:a["job"].update(run_attempt=1))
    def test_wrong_runner(self):self.reject(lambda a:a["job"].update(labels=["self-hosted"]))
    def test_wrong_repository(self):self.reject(lambda a:a["run"].update(head_repository={"full_name":"other/repo"}))
    def test_missing_marker(self):self.reject(lambda a:a.update(raw_log=a["raw_log"].replace(b"LFVM WORKBOOK TEST TEST-001 PASS\n",b"")))
    def test_duplicate_marker(self):self.reject(lambda a:a.update(raw_log=a["raw_log"]+b"LFVM WORKBOOK TEST TEST-001 PASS\n"))
    def test_metadata_not_workbook(self):self.reject(lambda a:a.update(raw_log=a["raw_log"]+b"FOUNDATION METADATA PASS\n"))
    def test_wrong_step(self):self.reject(lambda a:a["job"]["steps"][0].update(conclusion="failure"))
    def test_missing_git_store(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(Invalid):verify_git_inventory(Path(t),"template_schema","a"*40,"b"*40,"v0.0.0.1",Path(t),workflow_path=".github/workflows/template-workbook.yml",workflow_blob_sha="c"*40)

    def test_git_inventory_and_tamper(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            git_read(root,"init","-q")
            git_read(root,"config","user.name","Synthetic fixture")
            git_read(root,"config","user.email","fixture@example.org")
            git_read(root,"config","core.autocrlf","false")
            kind="template_schema"
            folder=root/CONFIG[kind][1]/"v0.0.0.1";folder.mkdir(parents=True)
            (folder/"README.md").write_bytes(b"synthetic candidate\n")
            workflow=".github/workflows/template-workbook.yml"
            (root/workflow).parent.mkdir(parents=True)
            (root/workflow).write_bytes(b"synthetic workflow, never executed\n")
            git_read(root,"add",".")
            git_read(root,"commit","-qm","synthetic inventory")
            sha=git_read(root,"rev-parse","HEAD").decode().strip()
            blob=git_read(root,"rev-parse",sha+":"+workflow).decode().strip()
            with patch.dict(ANCHORS,{kind:sha}):
                args=(root,kind,sha,sha,"v0.0.0.1",folder)
                kw={"workflow_path":workflow,"workflow_blob_sha":blob}
                self.assertEqual(len(verify_git_inventory(*args,**kw)),1)
                (folder/"README.md").write_bytes(b"changed")
                with self.assertRaises(Invalid):verify_git_inventory(*args,**kw)
