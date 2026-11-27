"""Synthetic negative/positive foundation fixtures; never real provider data."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from foundation import (BASE, BASE_DOCS, CONFIG, ROOT_DOCS, Invalid, validate, strict_json, version, verify_event, preflight_xlsx, safe_csv_text, streaming_sha256, verify_handoff_bytes)

CONTRACT = Path(__file__).resolve().parents[1] / "schemas" / "foundation-contract.json"


def write(path, obj):
    path.write_text(json.dumps(obj), encoding="utf-8")


def fixture(root, kind):
    branch, folder, vk, planned, _ = CONFIG[kind]
    status = "audit_pending" if kind == "template_schema" else "blocked_on_template"
    extra = ["TEMPLATE-LAWS.md"] if kind == "template_schema" else ["LIBRARY-LAWS.md","TEMPLATE-CONTRACT.md"]
    for name in (*ROOT_DOCS,*extra):
        (root/name).write_text("synthetic documentation\n", encoding="utf-8")
    (root/"schemas").mkdir()
    (root/"schemas"/"foundation-contract.json").write_bytes(CONTRACT.read_bytes())
    archive = root/folder
    d = archive/BASE
    d.mkdir(parents=True)
    for name in ("README.md","AGENTS.md","agent.md"):
        (archive/name).write_text("synthetic documentation\n", encoding="utf-8")
    docs = list(BASE_DOCS) + (["RECONCILIATION.md"] if kind == "research_data" else [])
    for name in docs:
        (d/name).write_text("synthetic documentation\n", encoding="utf-8")
    row = {"version":BASE,"path":BASE,"predecessor":None,"status":status,"locked":False}
    m = {"schema_version":1,vk:BASE,"predecessor":None,"status":status,"owner_locked":False,"validation":{"planned":planned,"executed":0,"passed":0},"documents":docs}
    if kind == "template_schema":
        row["artifact"] = None
        m.update(owner_implementation_approved=False, artifact=None, artifact_sha256=None, research_data_included=False, audit={"open":28,"closed":0})
    else:
        row["artifacts"] = []
        m.update(owner_import_approved=False,artifacts=[],template={"branch":CONFIG["template_schema"][0],"target_version":BASE,"accepted_version":None,"commit_sha":None,"artifact_path":None,"sha256":None},source_baseline={"expected_source_records":54,"imported_source_records":0,"unique_providers":None,"offer_count":None,"source_snapshot_sha256":None})
    index = {"schema_version":1,"branch":branch,"version_kind":kind,"active_version":BASE,"versions":[row]}
    write(archive/"versions.json",index)
    write(d/"manifest.json",m)
    return archive,d,index,m


class FoundationTests(unittest.TestCase):
    def case(self, kind, mutate=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a,d,i,m = fixture(root,kind)
            if mutate is not None:
                mutate(a,d,i,m)
                if (a/"versions.json").exists() and not (a/"versions.json").is_symlink():
                    write(a/"versions.json",i)
                if (d/"manifest.json").exists() and not (d/"manifest.json").is_symlink():
                    write(d/"manifest.json",m)
                with self.assertRaises((Invalid,OSError,ValueError,TypeError,KeyError)):
                    validate(root,kind)
            else:
                self.assertEqual(validate(root,kind),m)

    def both(self, mutate):
        for k in CONFIG:
            with self.subTest(kind=k):
                self.case(k,mutate)

    def test_baseline(self):
        for k in CONFIG:
            with self.subTest(kind=k):
                self.case(k)

    def test_active_pointer(self): self.both(lambda a,d,i,m:i.update(active_version=None))
    def test_wrong_branch(self): self.both(lambda a,d,i,m:i.update(branch="main"))
    def test_wrong_namespace(self): self.both(lambda a,d,i,m:i.update(version_kind="wrong"))
    def test_unknown_version(self): self.both(lambda a,d,i,m:i.update(schema_version=2))
    def test_boolean_schema(self): self.both(lambda a,d,i,m:i.update(schema_version=True))
    def test_missing_field(self): self.both(lambda a,d,i,m:m.pop("documents"))
    def test_extra_field(self): self.both(lambda a,d,i,m:m.update(approved=True))
    def test_empty_index(self): self.both(lambda a,d,i,m:i.update(versions=[]))
    def test_duplicate_version(self): self.both(lambda a,d,i,m:i["versions"].append(copy.deepcopy(i["versions"][0])))
    def test_path_traversal(self): self.both(lambda a,d,i,m:i["versions"][0].update(path="../outside"))
    def test_bad_predecessor(self): self.both(lambda a,d,i,m:i["versions"][0].update(predecessor=BASE))
    def test_wrong_version(self): self.both(lambda a,d,i,m:i["versions"][0].update(version="v00.0.0.1"))
    def test_unknown_status(self): self.both(lambda a,d,i,m:i["versions"][0].update(status="invented"))
    def test_unapproved_progress(self):
        def change(a,d,i,m):
            i["versions"][0]["status"]="implementing"
            m["status"]="implementing"
        self.both(change)
    def test_forged_lock(self):
        def change(a,d,i,m):
            i["versions"][0].update(status="locked",locked=True)
            m.update(status="locked",owner_locked=True)
        self.both(change)
    def test_lock_type(self): self.both(lambda a,d,i,m:m.update(owner_locked=0))
    def test_zero_tests(self): self.both(lambda a,d,i,m:m.update(validation={"planned":0,"executed":0,"passed":0}))
    def test_fake_pass(self): self.both(lambda a,d,i,m:m["validation"].update(passed=1,executed=1))
    def test_bool_counter(self): self.both(lambda a,d,i,m:m["validation"].update(passed=False))
    def test_doc_inventory(self): self.both(lambda a,d,i,m:m["documents"].append("OTHER.md"))
    def test_empty_doc(self): self.both(lambda a,d,i,m:(d/"PLAN.md").write_text(" \n",encoding="utf-8"))
    def test_missing_doc(self): self.both(lambda a,d,i,m:(d/"AUDIT.md").unlink())
    def test_unregistered_artifact(self): self.both(lambda a,d,i,m:(d/"fake.XLSX").write_bytes(b"not a workbook"))
    def test_nested_artifact(self):
        def change(a,d,i,m):
            (d/"hidden").mkdir()
            (d/"hidden"/"bad.xlsx").write_bytes(b"not a workbook")
        self.both(change)
    def test_unknown_archive_dir(self): self.both(lambda a,d,i,m:(a/"v00.0.0.2").mkdir())
    def test_blank_artifact_metadata(self): self.case("template_schema",lambda a,d,i,m:m.update(artifact="test.xlsx",artifact_sha256="0"*64))
    def test_blank_self_approval(self): self.case("template_schema",lambda a,d,i,m:m.update(owner_implementation_approved=True))
    def test_blank_audit_count(self): self.case("template_schema",lambda a,d,i,m:m.update(audit={"open":0,"closed":0}))
    def test_blank_research(self): self.case("template_schema",lambda a,d,i,m:m.update(research_data_included=True))
    def test_filled_self_approval(self): self.case("research_data",lambda a,d,i,m:m.update(owner_import_approved=True))
    def test_partial_template_binding(self): self.case("research_data",lambda a,d,i,m:m["template"].update(artifact_path="fake.xlsx"))
    def test_forged_template_digest(self): self.case("research_data",lambda a,d,i,m:m["template"].update(sha256="0"*64,commit_sha="0"*40,accepted_version=BASE))
    def test_source_count(self): self.case("research_data",lambda a,d,i,m:m["source_baseline"].update(expected_source_records=0))
    def test_fake_snapshot(self): self.case("research_data",lambda a,d,i,m:m["source_baseline"].update(source_snapshot_sha256="0"*64))
    def test_import_count(self): self.case("research_data",lambda a,d,i,m:m["source_baseline"].update(imported_source_records=54))
    def test_false_provider_count(self): self.case("research_data",lambda a,d,i,m:m["source_baseline"].update(unique_providers=54))
    def test_json_duplicate(self):
        with self.assertRaises(Invalid): strict_json(b'{"a":1,"a":2}')
    def test_json_nonfinite(self):
        with self.assertRaises(Invalid): strict_json(b'{"a":NaN}')
    def test_json_overflow_and_surrogate(self):
        for bad in (b'{"a":1e999}', b'{"a":-1e999}', b'{"a":"\\ud800"}'):
            with self.subTest(bad=bad),self.assertRaises(Invalid): strict_json(bad)
    def test_json_depth(self):
        with self.assertRaises(Invalid): strict_json(b"["*34+b"0"+b"]"*34)
    def test_contract_drift(self):
        for kind in CONFIG:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);fixture(root,kind)
                path=root/"schemas"/"foundation-contract.json"
                data=json.loads(path.read_bytes());data["publication"]["main_writes"]=True
                write(path,data)
                with self.assertRaises(Invalid): validate(root,kind)
    def test_json_limit(self):
        with self.assertRaises(Invalid): strict_json(b" "*262145)
    def test_version_grammar(self):
        for bad in ("v00.0.0.1","v1.2.3","v1.2.3.4\n","v1.2.3.-4",None):
            with self.subTest(bad=bad),self.assertRaises(Invalid): version(bad)
        self.assertEqual(version("v123456789.0.1.2"),"v123456789.0.1.2")
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            a,d,i,m=fixture(root,"template_schema")
            p=d/"PLAN.md"
            p.unlink()
            try: p.symlink_to(root/"README.md")
            except (OSError,NotImplementedError): self.skipTest("symlink privilege unavailable")
            with self.assertRaises(Invalid): validate(root,"template_schema")
    def test_handoff_crlf_checkout(self):
        original = b"a\nb\n"
        verify_handoff_bytes(original, original, original)
        verify_handoff_bytes(original, original, b"a\r\nb\r\n")

    def test_handoff_reject_changed_git_blob(self):
        with self.assertRaises(Invalid):
            verify_handoff_bytes(b"a\n", b"b\n", b"b\n")

    def test_handoff_reject_changed_checkout(self):
        with self.assertRaises(Invalid):
            verify_handoff_bytes(b"a\n", b"a\n", b"b\n")

    def test_event_context(self):
        for k,(branch,*_) in CONFIG.items():
            sha="a"*40
            env={"GITHUB_REPOSITORY":"vixttha/LFVM","GITHUB_SHA":sha,"GITHUB_EVENT_NAME":"push","GITHUB_REF":"refs/heads/"+branch}
            verify_event(env,k,sha)
            with self.assertRaises(Invalid): verify_event({**env,"GITHUB_REF":"refs/heads/main"},k,sha)
            with self.assertRaises(Invalid): verify_event({**env,"GITHUB_SHA":"b"*40},k,sha)
            verify_event({**env,"GITHUB_EVENT_NAME":"pull_request","GITHUB_BASE_REF":branch,"GITHUB_REF":"refs/pull/1/merge"},k,sha)
            with self.assertRaises(Invalid): verify_event({**env,"GITHUB_EVENT_NAME":"pull_request_target","GITHUB_BASE_REF":branch},k,sha)
    def test_csv_text(self):
        for v in ("=1+1","+1","-1","@SUM(A1)"," \t=1","\nabc","\uff1d1"):
            self.assertEqual(safe_csv_text(v),"'"+v)
        self.assertEqual(safe_csv_text("Oracle Cloud"),"Oracle Cloud")
        for value in ("\ufeff=1", "\u200b+1", "\u202e@SUM(A1)", " \u200b-1", "\uff0b1"):
            with self.subTest(value=value):
                self.assertEqual(safe_csv_text(value), "'" + value)
        with self.assertRaises(Invalid):
            safe_csv_text("x\x00y")


class PackageTests(unittest.TestCase):
    PARTS = {"[Content_Types].xml":'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>',"_rels/.rels":'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>',"xl/workbook.xml":'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>'}
    def package(self,changes=None,remove=None,good=False):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"synthetic.xlsx"
            parts=dict(self.PARTS)
            if changes: parts.update(changes)
            if remove: parts.pop(remove)
            with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED) as z:
                for name,content in parts.items(): z.writestr(name,content)
            if good: self.assertEqual(preflight_xlsx(p),streaming_sha256(p))
            else:
                with self.assertRaises((Invalid,ValueError,ETParseError,zipfile.BadZipFile)): preflight_xlsx(p)
    def test_minimal_package(self): self.package(good=True)
    def test_missing_part(self): self.package(remove="xl/workbook.xml")
    def test_zip_traversal(self): self.package({"../bad.xml":"<x/>"})
    def test_case_collision(self): self.package({"XL/WORKBOOK.XML":"<x/>"})
    def test_macro_part(self): self.package({"xl/vbaProject.xml":"<x/>"})
    def test_embedded_part(self): self.package({"xl/embeddings/x.xml":"<x/>"})
    def test_external_relationship(self): self.package({"_rels/.rels":'<Relationships><Relationship TargetMode="External" Target="https://example.org"/></Relationships>'})
    def test_missing_internal_target(self): self.package({"_rels/.rels":'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="urn:synthetic" Target="xl/absent.xml"/></Relationships>'})
    def test_internal_target(self): self.package({"_rels/.rels":'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="urn:synthetic" Target="xl/workbook.xml"/></Relationships>'},good=True)
    def test_duplicate_relationship_id(self): self.package({"_rels/.rels":'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="urn:synthetic" Target="xl/workbook.xml"/><Relationship Id="r1" Type="urn:synthetic" Target="xl/workbook.xml"/></Relationships>'})
    def test_xml_entity(self): self.package({"xl/workbook.xml":'<!DOCTYPE x [<!ENTITY y "unsafe">]><x/>'})
    def test_zip_ratio(self): self.package({"xl/big.xml":"<x>"+"a"*1000000+"</x>"})
    def test_active_xml_element(self):
        self.package({"xl/worksheets/sheet1.xml":'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><oleObjects/></worksheet>'})
    def test_auto_defined_name(self):
        self.package({"xl/workbook.xml":'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><definedNames><definedName name="Auto_Open">1</definedName></definedNames></workbook>'})
    def test_duplicate_content_type(self):
        self.package({"[Content_Types].xml":'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Default Extension="XML" ContentType="application/xml"/></Types>'})
    def test_orphan_override(self):
        self.package({"[Content_Types].xml":'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/xl/absent.xml" ContentType="application/xml"/></Types>'})
    def test_special_zip_file(self):
        import stat
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "synthetic.xlsx"
            with zipfile.ZipFile(p, "w") as z:
                for name, content in self.PARTS.items():
                    z.writestr(name, content)
                entry = zipfile.ZipInfo("xl/special.xml")
                entry.create_system = 3
                entry.external_attr = (stat.S_IFIFO | 0o600) << 16
                z.writestr(entry, "<x/>")
            with self.assertRaises(Invalid):
                preflight_xlsx(p)
    def test_invalid_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"not.xlsx"; p.write_bytes(b"not zip")
            with self.assertRaises(zipfile.BadZipFile): preflight_xlsx(p)

from xml.etree.ElementTree import ParseError as ETParseError
