"""Synthetic proof and data integrity tests. No production trust anchors or provider data."""
import base64
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from foundation import BASE, BASE_DOCS, CONFIG, Invalid
from qualification import (NAMESPACE, REPO, SUITES, artifact_inventory, canonical, digest,
    object_digest, payload, reconcile_sources, verify_dependency, verify_history,
    verify_partitions, verify_release, verify_signature, verify_transition, public_url,
    public_text, path_parts, validate_report)

import test_foundation


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys_dir=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.keys_dir.cleanup)
        root=Path(cls.keys_dir.name)
        cls.owner_private=root/"fixture_owner"
        cls.auditor_private=root/"fixture_auditor"
        for key in (cls.owner_private,cls.auditor_private):
            subprocess.run(["ssh-keygen","-q","-t","ed25519","-N","","-f",str(key)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        cls.owner_key=" ".join(Path(str(cls.owner_private)+".pub").read_text(encoding="utf-8").split()[:2])
        cls.auditor_key=" ".join(Path(str(cls.auditor_private)+".pub").read_text(encoding="utf-8").split()[:2])

    def sign(self,p,key):
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/"receipt.json"
            file.write_bytes(canonical(p))
            subprocess.run(["ssh-keygen","-Y","sign","-f",str(key),"-n",NAMESPACE,str(file)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
            sig=Path(str(file)+".sig").read_bytes()
            return {"payload":p,"signature":base64.b64encode(sig).decode("ascii")}

    def inputs(self,root,kind="template_schema",dependency=None):
        scope_bytes=b"synthetic scope only"
        schema_bytes=b"synthetic schema only"
        commit="a"*40 if kind=="template_schema" else "b"*40
        ctx={"repository":REPO,"branch":CONFIG[kind][0],"version_kind":kind,"version":BASE,"scope_sha256":digest(scope_bytes),"schema_sha256":digest(schema_bytes),"prior_acceptance_sha256":None,"template":dependency}
        folder=root/BASE
        folder.mkdir(parents=True)
        for name in (*BASE_DOCS,"manifest.json",*(("RECONCILIATION.md",) if kind=="research_data" else ())):
            (folder/name).write_text("synthetic fixture, not accepted research\n",encoding="utf-8")
        with zipfile.ZipFile(folder/"synthetic.xlsx","w") as z:
            for name,content in test_foundation.PackageTests.PARTS.items():
                z.writestr(name,content)
        report=[{"test_id":f"TEST-{i:03d}","status":"pass","run_id":1,"job_id":job,"evidence_sha256":"c"*64} for job in (2,3) for i in range(1,CONFIG[kind][3]+1)]
        def lookup(run,job):
            if run!=1 or job not in (2,3): return None
            return {"repository":REPO,"branch":CONFIG[kind][0],"commit_sha":commit,"event":"push","runner":"ubuntu-latest" if job==2 else "windows-latest","conclusion":"success","suite":SUITES[kind],"evidence_sha256":"c"*64,"test_ids":[r["test_id"] for r in report if r["job_id"]==job]}
        scope=self.sign(payload("scope_authorization",ctx),self.owner_private)
        binding={"candidate_commit":commit,"inventory_sha256":object_digest(artifact_inventory(folder)),"test_report_sha256":validate_report(report,kind,commit,lookup)}
        q=self.sign(payload("candidate_workbook_qualification",ctx,scope_receipt_sha256=object_digest(scope),binding=binding),self.auditor_private)
        a=self.sign(payload("owner_acceptance",ctx,scope_receipt_sha256=object_digest(scope),qualification_receipt_sha256=object_digest(q),binding=binding),self.owner_private)
        return dict(context=ctx,scope_bytes=scope_bytes,schema_bytes=schema_bytes,candidate_commit=commit,version_root=folder,report=report,run_lookup=lookup,owner_key=self.owner_key,auditor_key=self.auditor_key,scope_receipt=scope,qualification_receipt=q,acceptance_receipt=a,accepted_history=[])

    def template_binding(self,v):
        p,h,_=next(x for x in v.inventory if x[0].endswith(".xlsx"))
        return {"version":v.version,"commit_sha":v.commit_sha,"schema_sha256":v.schema_sha256,"acceptance_sha256":v.acceptance_sha256,"artifact_path":p,"artifact_sha256":h}

    def rejection(self,mutate):
        with tempfile.TemporaryDirectory() as t:
            args=self.inputs(Path(t))
            mutate(args)
            with self.assertRaises((Invalid,ValueError,OSError)):
                verify_release(**args)

    def test_signed_template(self):
        with tempfile.TemporaryDirectory() as t:
            args=self.inputs(Path(t))
            v=verify_release(**args)
            self.assertEqual(v.version,BASE)
            self.assertEqual(v.commit_sha,"a"*40)
            self.assertTrue(verify_dependency(self.template_binding(v),v))

    def test_signed_filled_dependency(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            v=verify_release(**self.inputs(root/"template"))
            binding=self.template_binding(v)
            args=self.inputs(root/"filled","research_data",binding)
            args["verified_template"]=v
            self.assertEqual(verify_release(**args).kind,"research_data")
            args["verified_template"]=None
            with self.assertRaises(Invalid): verify_release(**args)

    def test_owner_wrong_key(self):
        self.rejection(lambda a:a.update(owner_key=self.auditor_key))

    def test_auditor_wrong_signature(self):
        self.rejection(lambda a:a.update(qualification_receipt=self.sign(a["qualification_receipt"]["payload"],self.owner_private)))

    def test_missing_owner_signature(self):
        self.rejection(lambda a:a["acceptance_receipt"].update(signature=""))

    def test_tampered_payload(self):
        self.rejection(lambda a:a["acceptance_receipt"]["payload"]["binding"].update(candidate_commit="e"*40))

    def test_wrong_candidate(self):
        self.rejection(lambda a:a.update(candidate_commit="d"*40))

    def test_changed_scope(self):
        self.rejection(lambda a:a.update(scope_bytes=b"changed"))

    def test_changed_schema(self):
        self.rejection(lambda a:a.update(schema_bytes=b"changed"))

    def test_changed_artifact(self):
        self.rejection(lambda a:(a["version_root"]/"README.md").write_text("changed",encoding="utf-8"))

    def test_missing_test(self):
        self.rejection(lambda a:a["report"].pop())

    def test_duplicate_test(self):
        self.rejection(lambda a:a["report"].append(copy.deepcopy(a["report"][0])))

    def test_metadata_suite_not_qualification(self):
        def change(a):
            old=a["run_lookup"]
            a["run_lookup"]=lambda r,j:{**old(r,j),"suite":"foundation_metadata"}
        self.rejection(change)

    def test_unrelated_runner_commit(self):
        def change(a):
            old=a["run_lookup"]
            a["run_lookup"]=lambda r,j:{**old(r,j),"commit_sha":"e"*40}
        self.rejection(change)

    def test_incomplete_platform_coverage(self):
        def change(a):
            old=a["run_lookup"]
            a["run_lookup"]=lambda r,j:({**old(r,j),"test_ids":old(r,j)["test_ids"][:-1]} if j==2 else old(r,j))
        self.rejection(change)

    def test_missing_platform(self):
        def change(a):
            old=a["run_lookup"]
            a["run_lookup"]=lambda r,j:{**old(r,j),"runner":"ubuntu-latest"}
        self.rejection(change)

    def test_unavailable_runner_evidence(self):
        self.rejection(lambda a:a.update(run_lookup=lambda r,j:None))

    def test_history_integrity(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            args=self.inputs(root)
            v=verify_release(**args)
            nxt={**args["context"],"version":"v0.0.0.2","prior_acceptance_sha256":v.acceptance_sha256}
            self.assertTrue(verify_history(root,[v],nxt))
            (root/BASE/"CHANGES.md").write_text("edited",encoding="utf-8")
            with self.assertRaises(Invalid): verify_history(root,[v],nxt)

    def test_history_missing_accepted_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            args=self.inputs(root)
            v=verify_release(**args)
            nxt={**args["context"],"version":"v0.0.0.2","prior_acceptance_sha256":v.acceptance_sha256}
            shutil.rmtree(root/BASE)
            with self.assertRaises(OSError): verify_history(root,[v],nxt)

    def test_history_wrong_predecessor(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            args=self.inputs(root)
            v=verify_release(**args)
            with self.assertRaises(Invalid): verify_history(root,[v],{**args["context"],"version":"v0.0.0.2","prior_acceptance_sha256":"e"*64})

    def test_template_binding_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            v=verify_release(**self.inputs(Path(t)))
            binding=self.template_binding(v)
            binding["artifact_sha256"]="e"*64
            with self.assertRaises(Invalid): verify_dependency(binding,v)


class DataBoundaryTests(unittest.TestCase):
    def test_transition_authorization(self):
        with self.assertRaises(Invalid): verify_transition("template_schema","planned","approved")
        self.assertTrue(verify_transition("template_schema","planned","approved",scope_verified=True))
        with self.assertRaises(Invalid): verify_transition("template_schema","qualified","locked",scope_verified=True,qualification_verified=True)
        self.assertTrue(verify_transition("template_schema","qualified","locked",scope_verified=True,qualification_verified=True,acceptance_verified=True))
        with self.assertRaises(Invalid): verify_transition("template_schema","locked","implementing",scope_verified=True)

    def test_transition_template_dependency(self):
        with self.assertRaises(Invalid): verify_transition("research_data","blocked_on_template","planned")
        self.assertTrue(verify_transition("research_data","blocked_on_template","planned",template_verified=True))

    def test_path_safety(self):
        for s in ("../bad.xlsx","a\\b.xlsx","/bad.xlsx","x/\u202efile.xlsx","a/CON.xlsx","a/b."):
            with self.subTest(s=s),self.assertRaises(Invalid): path_parts(s)
        self.assertEqual(path_parts("partitions/a.xlsx"),["partitions","a.xlsx"])

    def test_public_urls(self):
        for value in ("http://example.org","https://localhost/x","https://127.0.0.1","https://10.0.0.1","https://app.notion.com/p/private","https://user:pass@example.org","https://example.org?api_key=secret"):
            with self.subTest(value=value),self.assertRaises(Invalid): public_url(value)
        self.assertTrue(public_url("https://example.org/pricing"))

    def test_public_url_fragment_and_encoded_credential(self):
        for value in ("https://example.org/#access_token=fixture","https://example.org:bad/","https://example.org/%0a","https://example.org/ghp%5f"+"a"*36):
            with self.subTest(value=value),self.assertRaises(Invalid): public_url(value)

    def test_public_text(self):
        with self.assertRaises(Invalid): public_text("ghp_"+("a"*36))
        with self.assertRaises(Invalid): public_text("see https://example.org?token=placeholder")
        self.assertTrue(public_text("public research URL https://example.org/pricing"))

    def source_fixture(self):
        originals=[{"source_id":f"src-{i}","original":{"title":f"synthetic source {i}","url":"https://example.org"}} for i in range(54)]
        snapshot=canonical({"schema_version":1,"records":originals})
        mappings=[{"source_id":r["source_id"],"original_sha256":object_digest(r["original"]),"disposition":"imported","target_offer_ids":[f"offer-{i}"],"reason":"synthetic test"} for i,r in enumerate(originals)]
        offers={f"offer-{i}" for i in range(54)}
        return snapshot,mappings,offers

    def test_source_all_accounted(self):
        s,m,o=self.source_fixture()
        m[0].update(disposition="excluded",target_offer_ids=[])
        o.remove("offer-0")
        result=reconcile_sources(s,digest(s),m,o)
        self.assertEqual((result["accounted"],result["imported"],result["excluded"],result["normalized_offer_count"]),(54,53,1,53))

    def test_source_missing_mapping(self):
        s,m,o=self.source_fixture()
        with self.assertRaises(Invalid): reconcile_sources(s,digest(s),m[:-1],o)

    def test_source_duplicate_mapping(self):
        s,m,o=self.source_fixture()
        with self.assertRaises(Invalid): reconcile_sources(s,digest(s),m+[m[0]],o)

    def test_source_digest(self):
        s,m,o=self.source_fixture()
        with self.assertRaises(Invalid): reconcile_sources(s,"0"*64,m,o)

    def test_source_original_hash(self):
        s,m,o=self.source_fixture()
        m[0]["original_sha256"]="0"*64
        with self.assertRaises(Invalid): reconcile_sources(s,digest(s),m,o)

    def test_source_unknown_offer(self):
        s,m,o=self.source_fixture()
        m[0]["target_offer_ids"]=["not-present"]
        with self.assertRaises(Invalid): reconcile_sources(s,digest(s),m,o)

    def test_source_unmapped_offer(self):
        s,m,o=self.source_fixture()
        o.add("unmapped")
        with self.assertRaises(Invalid): reconcile_sources(s,digest(s),m,o)

    def test_source_secret(self):
        s,m,o=self.source_fixture()
        obj=json.loads(s)
        obj["records"][0]["original"]["title"]="ghp_"+("a"*36)
        s=canonical(obj)
        m[0]["original_sha256"]=object_digest(obj["records"][0]["original"])
        with self.assertRaises(Invalid): reconcile_sources(s,digest(s),m,o)

    def test_partition_scale_and_duplicate(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            rows=[]
            for i,size in enumerate((100,1000,10000)):
                p=root/f"partition-{i}.json"
                p.write_bytes(canonical([f"p{i}:{j}" for j in range(size)]))
                rows.append({"path":p.name,"sha256":digest(p.read_bytes()),"record_count":size})
            parser=lambda p:json.loads(p.read_bytes())
            self.assertEqual(verify_partitions(root,rows,parser),11100)
            p=root/"partition-1.json"
            values=parser(p)
            values[0]="p0:0"
            p.write_bytes(canonical(values))
            rows[1]["sha256"]=digest(p.read_bytes())
            with self.assertRaises(Invalid): verify_partitions(root,rows,parser)

    def test_partition_scalar_parser(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=root/"p.json";p.write_bytes(b"abc")
            with self.assertRaises(Invalid): verify_partitions(root,[{"path":p.name,"sha256":digest(p.read_bytes()),"record_count":3}],lambda p:"abc")

    def test_partition_count(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);p=root/"p.json";p.write_bytes(b'["a"]')
            with self.assertRaises(Invalid): verify_partitions(root,[{"path":"p.json","sha256":digest(p.read_bytes()),"record_count":2}],lambda p:json.loads(p.read_bytes()))
