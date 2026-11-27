"""Synthetic-only qualification and recovery regressions."""
from datetime import date
from pathlib import Path
import copy
import sys
import tempfile
import unittest
import zipfile
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from foundation import Invalid
from qualification import artifact_inventory, canonical, digest
from draft_qualification import evidence_check, read_draft_xlsx, read_partitioned_library, publish_staged_pointer, verify_migration, M, R, P, T, col_name
from test_draft_records import SCHEMA, fixture, row, uid

DAY=date(2026,1,10)
def evidence_fixture():
    d=fixture()
    # Mark all material values unknown except the explicitly documented environment
    # and resource measurement, with exact typed official evidence.
    for i,(table,rid,field,value) in enumerate((
        ("05_OFFERS",uid(3),"environment","vm"),
        ("06_RESOURCES",uid(5),"value_min",4),
        ("06_RESOURCES",uid(5),"unit","GiB"),
        ("06_RESOURCES",uid(5),"guarantee","typical"),
    ),20):
        d["09_EVIDENCE"].append(row("09_EVIDENCE",evidence_id=uid(i),claim_id=uid(i+100),target_table=table,target_id=rid,field_name=field,claimed_value=canonical(value).decode(),source_url="https://example.org/fixture",retrieved_on="2026-01-01",review_due="2026-01-20",grade="E3",outcome="supports"))
    return d

class EvidenceTests(unittest.TestCase):
    def reject(self,edit):
        d=evidence_fixture();edit(d)
        with self.assertRaises(Invalid):evidence_check(SCHEMA,d,DAY)
    def test_current(self):
        self.assertEqual(evidence_check(SCHEMA,evidence_fixture(),DAY)["material_fields_covered"],4)
    def test_missing(self):self.reject(lambda d:d["09_EVIDENCE"].pop())
    def test_mismatch(self):self.reject(lambda d:d["09_EVIDENCE"][1].update(claimed_value="5"))
    def test_wrong_type(self):self.reject(lambda d:d["09_EVIDENCE"][1].update(claimed_value="true"))
    def test_expired(self):self.reject(lambda d:d["09_EVIDENCE"][0].update(review_due="2026-01-02"))
    def test_future_retrieval(self):self.reject(lambda d:d["09_EVIDENCE"][0].update(retrieved_on="2026-01-11"))
    def test_future_effective(self):self.reject(lambda d:d["09_EVIDENCE"][0].update(effective_on="2026-01-11"))
    def test_excessive_review(self):self.reject(lambda d:d["09_EVIDENCE"][0].update(review_due="2027-01-01"))
    def test_low_grade(self):self.reject(lambda d:d["09_EVIDENCE"][0].update(grade="E1"))
    def test_conflict(self):
        def edit(d):
            e=copy.deepcopy(d["09_EVIDENCE"][0]);e.update(evidence_id=uid(90),outcome="contradicts",claimed_value='"container"');d["09_EVIDENCE"].append(e)
        self.reject(edit)
    def test_claim_identity(self):
        def edit(d):
            e=copy.deepcopy(d["09_EVIDENCE"][0]);e.update(evidence_id=uid(90),claim_id=uid(91));d["09_EVIDENCE"].append(e)
        self.reject(edit)

def package(path,data=None,mutate=None,partition_offset=0,dataset=999,edition="v0.0.0.1"):
    """Build disposable OOXML test fixture, never a release artifact."""
    parts={}
    def root(tag,**attrs):return ET.Element(tag,attrs)
    def put(name,element):parts[name]=element
    ct="{http://schemas.openxmlformats.org/package/2006/content-types}"
    types=root(ct+"Types")
    ET.SubElement(types,ct+"Default",Extension="xml",ContentType="application/xml")
    ET.SubElement(types,ct+"Default",Extension="rels",ContentType="application/vnd.openxmlformats-package.relationships+xml")
    put("[Content_Types].xml",types)
    package_rels=root(P+"Relationships")
    ET.SubElement(package_rels,P+"Relationship",Id="rId1",Type=T+"officeDocument",Target="xl/workbook.xml")
    put("_rels/.rels",package_rels)
    workbook=root(M+"workbook");sheets=ET.SubElement(workbook,M+"sheets")
    workbook_rels=root(P+"Relationships")
    tables={t["sheet"]:t for t in SCHEMA["tables"]}
    contents=copy.deepcopy(data or {})
    contents["02_DICTIONARY"]=[row("02_DICTIONARY",field_id=name+"."+c["name"],table_name=name,column_name=c["name"],data_type=c["type"],required=c["required"],description=c["description"],foreign_key=t.get("foreign_keys",{}).get(c["name"])) for name,t in tables.items() for c in t["columns"]]
    contents["03_TAXONOMY"]=[row("03_TAXONOMY",taxonomy_id=family+":"+code,family=family,code=code,display_label=code,definition="Synthetic definition",deprecated=False) for family,values in SCHEMA["enums"].items() for code in values]
    contents["01_MANIFEST"]=[row("01_MANIFEST",partition_id=uid(1000+i+partition_offset),dataset_id=uid(dataset),schema_version=SCHEMA["template_version"],data_version=None if data is None else edition,relative_path=path.name,table_name=name,record_count=len(tables) if name=="01_MANIFEST" else len(contents.get(name,[])),partition_state="active") for i,name in enumerate(tables)]
    ET.SubElement(types,ct+"Override",PartName="/xl/workbook.xml",ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml")
    def add_cell(rr,i,n,v):
        if v is None:return
        c=ET.SubElement(rr,M+"c",r=col_name(i)+str(n))
        if type(v) is str:
            c.set("t","inlineStr");ET.SubElement(ET.SubElement(c,M+"is"),M+"t").text=v
        elif type(v) is bool:
            c.set("t","b");ET.SubElement(c,M+"v").text="1" if v else "0"
        else:ET.SubElement(c,M+"v").text=str(v)
    for i,name in enumerate(SCHEMA["sheet_order"],1):
        rid=f"rId{i}";sp=f"xl/worksheets/sheet{i}.xml"
        ET.SubElement(sheets,M+"sheet",{"name":name,"sheetId":str(i),R+"id":rid})
        ET.SubElement(workbook_rels,P+"Relationship",Id=rid,Type=T+"worksheet",Target=f"worksheets/sheet{i}.xml")
        ws=root(M+"worksheet");sd=ET.SubElement(ws,M+"sheetData")
        put(sp,ws)
        ET.SubElement(types,ct+"Override",PartName="/"+sp,ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml")
        if name=="00_README":
            add_cell(ET.SubElement(sd,M+"row",r="1"),1,1,"Synthetic fixture");continue
        headers=[c["name"] for c in tables[name]["columns"]]
        rr=ET.SubElement(sd,M+"row",r="1")
        for j,h in enumerate(headers,1):add_cell(rr,j,1,h)
        content=contents.get(name,[])
        for k,record in enumerate(content,2):
            rr=ET.SubElement(sd,M+"row",r=str(k))
            for j,h in enumerate(headers,1):add_cell(rr,j,k,record[h])
        tp=ET.SubElement(ws,M+"tableParts",count="1")
        ET.SubElement(tp,M+"tablePart",{R+"id":"rId1"})
        sr=root(P+"Relationships")
        ET.SubElement(sr,P+"Relationship",Id="rId1",Type=T+"table",Target=f"../tables/table{i}.xml")
        put(f"xl/worksheets/_rels/sheet{i}.xml.rels",sr)
        table=root(M+"table",id=str(i),name=f"Table{i}",displayName=f"Table{i}",ref="A1:"+col_name(len(headers))+str(len(content)+1))
        tc=ET.SubElement(table,M+"tableColumns",count=str(len(headers)))
        for j,h in enumerate(headers,1):ET.SubElement(tc,M+"tableColumn",id=str(j),name=h)
        put(f"xl/tables/table{i}.xml",table)
        ET.SubElement(types,ct+"Override",PartName=f"/xl/tables/table{i}.xml",ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml")
    put("xl/workbook.xml",workbook);put("xl/_rels/workbook.xml.rels",workbook_rels)
    if mutate:mutate(parts)
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as z:
        for n,p in parts.items():z.writestr(n,ET.tostring(p,encoding="utf-8"))

class WorkbookTests(unittest.TestCase):
    def run_case(self,mutate=None,data=None,blank=True,good=False):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"synthetic.xlsx";package(p,data,mutate)
            if good:return read_draft_xlsx(p,SCHEMA,blank=blank)
            with self.assertRaises(Invalid):read_draft_xlsx(p,SCHEMA,blank=blank)
    def test_blank(self):
        proof=self.run_case(good=True)
        self.assertEqual(sum(proof["table_rows"][k] for k in proof["research"]),0)
        self.assertEqual(proof["table_rows"]["02_DICTIONARY"],149)
        self.assertEqual(proof["table_rows"]["01_MANIFEST"],11)
    def test_filled(self):self.assertEqual(self.run_case(data=fixture(),blank=False,good=True)["research"],fixture())
    def test_data_in_blank(self):self.run_case(data=fixture())
    def test_wrong_name(self):self.run_case(lambda p:p["xl/workbook.xml"].find(M+"sheets")[0].set("name","wrong"))
    def test_hidden_sheet(self):self.run_case(lambda p:p["xl/workbook.xml"].find(M+"sheets")[0].set("state","hidden"))
    def test_header(self):self.run_case(lambda p:p["xl/worksheets/sheet5.xml"].find(".//"+M+"t").__setattr__("text","wrong"))
    def test_table_range(self):self.run_case(lambda p:p["xl/tables/table5.xml"].set("ref","A1:A2"))
    def test_table_header_metadata(self):self.run_case(lambda p:p["xl/tables/table5.xml"].find(M+"tableColumns")[0].set("name","wrong"))
    def test_formula(self):self.run_case(lambda p:ET.SubElement(p["xl/worksheets/sheet5.xml"].find(".//"+M+"c"),M+"f").__setattr__("text","1+1"))
    def test_hidden_row(self):self.run_case(lambda p:p["xl/worksheets/sheet5.xml"].find(".//"+M+"row").set("hidden","1"))
    def test_orphan(self):self.run_case(lambda p:p.update({"xl/worksheets/orphan.xml":ET.Element(M+"worksheet")}))
    def test_duplicate_cell(self):
        def mutate(p):
            rr=p["xl/worksheets/sheet5.xml"].find(".//"+M+"row");rr.append(copy.deepcopy(rr[0]))
        self.run_case(mutate)
    def test_dictionary_mismatch(self):
        self.run_case(lambda p:p["xl/worksheets/sheet3.xml"].find(M+"sheetData")[1].find(".//"+M+"t").__setattr__("text","wrong"))
    def test_taxonomy_mismatch(self):
        self.run_case(lambda p:p["xl/worksheets/sheet4.xml"].find(M+"sheetData")[1].find(".//"+M+"t").__setattr__("text","wrong"))
    def test_manifest_count_mismatch(self):
        def change(p):
            rr=p["xl/worksheets/sheet2.xml"].find(M+"sheetData")[1]
            next(c for c in rr if c.get("r")=="G2").find(M+"v").text="999"
        self.run_case(change)
    def test_root_relationship(self):
        self.run_case(lambda p:p["_rels/.rels"][0].set("Type","urn:wrong"))
    def test_content_type(self):
        def change(p):
            next(n for n in p["[Content_Types].xml"] if n.get("PartName")=="/xl/workbook.xml").set("ContentType","application/xml")
        self.run_case(change)
    def test_duplicate_table_identity(self):
        self.run_case(lambda p:p["xl/tables/table5.xml"].set("displayName","Table4"))
    def test_merged(self):self.run_case(lambda p:ET.SubElement(p["xl/worksheets/sheet5.xml"],M+"mergeCells"))

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.old=b'{"edition":"previous"}';(self.root/"current.json").write_bytes(self.old)
        self.stage=self.root/"candidate";self.stage.mkdir();(self.stage/"data.json").write_text("{}",encoding="utf-8")
        self.inventory=artifact_inventory(self.stage)
    def publish(self,inject=None):
        return publish_staged_pointer(self.root,self.old,"candidate",self.inventory,inject=inject)
    def test_success(self):self.assertEqual(self.publish(),(self.root/"current.json").read_bytes())
    def test_stale(self):
        (self.root/"current.json").write_bytes(b"changed")
        with self.assertRaises(Invalid):self.publish()
        self.assertEqual((self.root/"current.json").read_bytes(),b"changed")
    def test_locked(self):
        (self.root/".publish.lock").write_bytes(b"existing")
        with self.assertRaises(FileExistsError):self.publish()
        self.assertEqual((self.root/".publish.lock").read_bytes(),b"existing")
    def test_failure(self):
        def fail(stage):
            if stage=="before_replace":raise RuntimeError("synthetic interruption")
        with self.assertRaises(RuntimeError):self.publish(fail)
        self.assertEqual((self.root/"current.json").read_bytes(),self.old)
        self.assertFalse((self.root/".publish.lock").exists())
        self.assertEqual(list(self.root.glob(".pointer-*")),[])
    def test_modified_stage(self):
        def edit(stage):
            if stage=="before_replace":(self.stage/"data.json").write_text('{"changed":true}',encoding="utf-8")
        with self.assertRaises(Invalid):self.publish(edit)
        self.assertEqual((self.root/"current.json").read_bytes(),self.old)
    def test_migration_missing_sources(self):
        data=evidence_fixture();snap=canonical({"schema_version":1,"records":[]})
        with self.assertRaises(Invalid):verify_migration(SCHEMA,snap,digest(snap),[],{k:[] for k in data},data,DAY)
    def test_migration_54(self):
        data=evidence_fixture()
        records=[{"source_id":f"source-{i}","original":{"name":f"Synthetic {i}"}} for i in range(54)]
        snap=canonical({"schema_version":1,"records":records})
        ledger=[{"source_id":r["source_id"],"original_sha256":digest(canonical(r["original"])),"disposition":"imported" if i==0 else "duplicate","target_offer_ids":[uid(3)],"reason":"Synthetic fixture"} for i,r in enumerate(records)]
        self.assertEqual(verify_migration(SCHEMA,snap,digest(snap),ledger,{k:[] for k in data},data,DAY)["accounted"],54)
        source=copy.deepcopy(data);source["05_OFFERS"][0]["offer_name"]="Prior retained offer"
        with self.assertRaises(Invalid):verify_migration(SCHEMA,snap,digest(snap),ledger,source,data,DAY)


class MultiWorkbookTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.data=evidence_fixture()
    def write(self, duplicate=False, offset=100, dataset=999, edition="v0.0.0.1", drop_provider=False):
        first={k:[] for k in self.data};second=copy.deepcopy(self.data)
        first["04_PROVIDERS"]=second["04_PROVIDERS"]
        if not duplicate:second["04_PROVIDERS"]=[]
        if drop_provider:first["04_PROVIDERS"]=[]
        package(self.root/"a.xlsx",first)
        package(self.root/"b.xlsx",second,partition_offset=offset,dataset=dataset,edition=edition)
        entries=[]
        for p,rows in [(self.root/"a.xlsx",first),(self.root/"b.xlsx",second)]:
            entries.append({"path":p.name,"sha256":digest(p.read_bytes()),"size_bytes":p.stat().st_size,
              "table_rows":{**{k:len(v) for k,v in rows.items()},"01_MANIFEST":11,"02_DICTIONARY":149,
              "03_TAXONOMY":sum(len(v) for v in SCHEMA["enums"].values())}})
        return {"schema_sha256":digest(canonical(SCHEMA)),"dataset_id":uid(999),"data_version":"v0.0.0.1",
                "files":entries,"global_counts":{k:len(v) for k,v in self.data.items()}}
    def verify(self,index):
        raw=canonical(index)
        return read_partitioned_library(self.root,SCHEMA,raw,digest(raw),DAY)
    def test_cross_workbook_references(self):
        self.assertEqual(self.verify(self.write())["research"],self.data)
    def test_duplicate_global_record(self):
        with self.assertRaises(Invalid):self.verify(self.write(duplicate=True))
    def test_duplicate_partition(self):
        with self.assertRaises(Invalid):self.verify(self.write(offset=0))
    def test_different_dataset(self):
        with self.assertRaises(Invalid):self.verify(self.write(dataset=998))
    def test_different_edition(self):
        with self.assertRaises(Invalid):self.verify(self.write(edition="v0.0.0.2"))
    def test_missing_provider(self):
        with self.assertRaises(Invalid):self.verify(self.write(drop_provider=True))
    def test_unregistered_file(self):
        index=self.write();(self.root/"unregistered.xlsx").write_bytes(b"x")
        with self.assertRaises(Invalid):self.verify(index)
    def test_wrong_digest(self):
        index=self.write();index["files"][0]["sha256"]="0"*64
        with self.assertRaises(Invalid):self.verify(index)
    def test_wrong_global_count(self):
        index=self.write();index["global_counts"]["05_OFFERS"]=99
        with self.assertRaises(Invalid):self.verify(index)
    def test_wrong_local_count(self):
        index=self.write();index["files"][0]["table_rows"]["04_PROVIDERS"]=99
        with self.assertRaises(Invalid):self.verify(index)
    def test_untrusted_index(self):
        raw=canonical(self.write())
        with self.assertRaises(Invalid):read_partitioned_library(self.root,SCHEMA,raw,"0"*64,DAY)
    def test_schema_mismatch(self):
        index=self.write();index["schema_sha256"]="0"*64
        with self.assertRaises(Invalid):self.verify(index)
