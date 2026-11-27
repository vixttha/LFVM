"""Synthetic independently supplied GitHub evidence regression cases."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from foundation import CONFIG, Invalid
from operations import PLATFORMS, PYTHONS, REPO, PATHS, REQUIRED_STEPS, verify_foundation_run

class OperationsTests(unittest.TestCase):
    def fixture(self, kind="template_schema"):
        sha="a"*40
        run={"id":17,"run_attempt":2,"path":PATHS[kind],"head_branch":CONFIG[kind][0],"head_sha":sha,
             "event":"push","status":"completed","conclusion":"success",
             "repository":{"full_name":REPO},"head_repository":{"full_name":REPO}}
        jobs=[]; logs={}
        for idx,(os_name,p) in enumerate(((o,p) for o in PLATFORMS for p in PYTHONS),1):
            jobs.append({"id":idx,"name":f"foundation ({os_name}, {p})","run_id":17,"run_attempt":2,
                         "head_sha":sha,"status":"completed","conclusion":"success","labels":[os_name],
                         "steps":[{"name":s,"status":"completed","conclusion":"success"} for s in REQUIRED_STEPS]})
            identity=f"CI identity: {sha}; event=push; Python={p}.7; platform={'linux' if os_name=='ubuntu-latest' else 'win32'}"
            gate=f"FOUNDATION METADATA PASS: {kind}; pre-build only; release and workbook qualification disabled"
            logs[idx]=(f"{identity}\n{gate}\nRan 150 tests in 1.00s\nOK\nRan 150 tests in 2.00s\nOK\n{identity}\n{gate}\n").encode()
        return dict(kind=kind,sha=sha,run=run,jobs=jobs,log_lookup=lambda r,a,j:logs[j],minimum_tests=150),logs
    def reject(self, edit):
        args,logs=self.fixture()
        edit(args,logs)
        with self.assertRaises(Invalid): verify_foundation_run(**args)
    def test_full_matrix(self):
        for kind in CONFIG:
            a,_=self.fixture(kind)
            proof=verify_foundation_run(**a)
            self.assertEqual(len(proof["jobs"]),4)
            self.assertFalse(proof["workbook_qualified"])
            self.assertFalse(proof["owner_approved"])
    def test_wrong_commit(self): self.reject(lambda a,l:a["run"].update(head_sha="b"*40))
    def test_wrong_branch(self): self.reject(lambda a,l:a["run"].update(head_branch="main"))
    def test_wrong_workflow(self): self.reject(lambda a,l:a["run"].update(path=".github/workflows/other.yml"))
    def test_fork(self): self.reject(lambda a,l:a["run"].update(head_repository={"full_name":"other/repo"}))
    def test_pr(self): self.reject(lambda a,l:a["run"].update(event="pull_request"))
    def test_failed_run(self): self.reject(lambda a,l:a["run"].update(conclusion="failure"))
    def test_incomplete_matrix(self): self.reject(lambda a,l:a["jobs"].pop())
    def test_duplicate_job(self): self.reject(lambda a,l:a["jobs"].__setitem__(0,copy.deepcopy(a["jobs"][1])))
    def test_wrong_attempt(self): self.reject(lambda a,l:a["jobs"][0].update(run_attempt=1))
    def test_wrong_job_commit(self): self.reject(lambda a,l:a["jobs"][0].update(head_sha="b"*40))
    def test_wrong_runner(self): self.reject(lambda a,l:a["jobs"][0].update(labels=["self-hosted"]))
    def test_failed_step(self): self.reject(lambda a,l:a["jobs"][0]["steps"][0].update(conclusion="failure"))
    def test_missing_step(self): self.reject(lambda a,l:a["jobs"][0]["steps"].pop())
    def test_missing_log(self): self.reject(lambda a,l:l.update({1:b""}))
    def test_wrong_python(self): self.reject(lambda a,l:l.update({1:l[1].replace(b"3.11.7",b"3.12.7")}))
    def test_wrong_identity(self): self.reject(lambda a,l:l.update({1:l[1].replace(b"a"*40,b"b"*40)}))
    def test_test_count(self): self.reject(lambda a,l:l.update({1:l[1].replace(b"150 tests",b"149 tests")}))
    def test_skipped(self): self.reject(lambda a,l:l.update({1:l[1].replace(b"OK\n",b"OK (skipped=1)\n")}))
    def test_metadata_only(self): self.reject(lambda a,l:l.update({1:l[1].replace(b"Ran 150 tests in 1.00s\nOK\n",b"")}))
    def test_qualification_not_substitutable(self): self.reject(lambda a,l:l.update({1:l[1].replace(b"FOUNDATION METADATA PASS",b"WORKBOOK PASS")}))
