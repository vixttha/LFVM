"""Strict qualification of the draft schema, synthetic workbook and staged migration.

This is not a release authority. All production gates remain disabled.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import json
import math
import os
import re
import tempfile
import zipfile
from xml.etree import ElementTree as ET

from foundation import Invalid, require, strict_json, preflight_xlsx, streaming_sha256, regular, read_bytes, portable_name
from qualification import canonical, digest, public_text, reconcile_sources, artifact_inventory
from draft_records import validate_records, scalar, RESEARCH, check_id
from qualification import path_parts
from foundation import version
from workbook_design import validate_design

M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
P = "{http://schemas.openxmlformats.org/package/2006/relationships}"
T = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
CELL = re.compile(r"([A-Z]{1,3})([1-9][0-9]*)\Z")
MAX_ROWS = 100000
MIN_GRADE = {"E0":0,"E1":1,"E2":2,"E3":3,"E4":4,"E5":5,"E6":6}
UNKNOWN = ("unknown","unverified","Unverified","F0","U","RU","unassessed")
# Historical taxonomy labels, internal IDs and review bookkeeping are not claims of current availability.
MATERIAL = {
    "04_PROVIDERS": ("official_url","country","status"),
    "05_OFFERS": ("environment","availability","execution","funding","eligibility","expiration",
                   "expiry_date","duration_count","duration_unit","renewable","permanent_free","custom_code",
                   "commercial_use","llm_use","signup_url","terms_url","currency","card_required",
                   "deposit_state","setup_fee_state","recurring_fee_state","storage_fee_state","network_fee_state",
                   "overage_fee_state","renewal_fee_state","billing_cap","auto_upgrade","zero_cost_verified"),
    "06_RESOURCES": ("value_min","value_max","value_text","unit","period_count","period_unit","guarantee","region_code"),
    "07_COMPATIBILITY": ("status","test_date","test_commit","benchmark_metric","benchmark_value","benchmark_unit"),
    "08_ASSESSMENTS": ("trust_grade","billing_risk","risk","suitability"),
}

def equal_value(a,b):
    # bool must never be confused with numeric zero/one.
    return type(a) is type(b) and a == b

def review_days(table, field):
    if table == "04_PROVIDERS" and field in {"official_url","country"}:
        return 365
    if table == "06_RESOURCES":
        return 90
    return 30

def evidence_check(schema, data, as_of):
    """Prove internal claim coverage and freshness, not actual source truth."""
    validate_design(schema)
    validate_records(schema,data)
    require(type(as_of) is date,"explicit review date required")
    tables={t["sheet"]:t for t in schema["tables"]}
    index={(t,r[tables[t]["primary_key"]]):r for t in RESEARCH for r in data[t]}
    columns={t:{c["name"]:c for c in tables[t]["columns"]} for t in RESEARCH}
    evidence={}
    claim_identity={}
    for e in data["09_EVIDENCE"]:
        key=(e["target_table"],e["target_id"],e["field_name"])
        require(key not in claim_identity or claim_identity[key]==e["claim_id"],"multiple claim identities for one field")
        claim_identity[key]=e["claim_id"]
        val=strict_json(e["claimed_value"].encode("utf-8"))
        col=columns[key[0]][key[2]]
        if val is not None:
            scalar(val,col["type"],schema["enums"])
        retrieved=date.fromisoformat(e["retrieved_on"])
        due=date.fromisoformat(e["review_due"])
        require(retrieved<=as_of,"future evidence retrieval")
        for f in ("published_on","effective_on"):
            if e[f] is not None:
                require(date.fromisoformat(e[f])<=as_of,"future evidence date")
        require(due<=retrieved+timedelta(days=review_days(key[0],key[2])),"excessive evidence review interval")
        if e["outcome"]=="supports" and due>=as_of and MIN_GRADE[e["grade"]]>=3:
            require(equal_value(val,index[key[:2]][key[2]]),"current supporting claim disagrees with canonical value")
        evidence.setdefault(key,[]).append((e,val,retrieved,due))
    covered=0
    for (table,rid),row in index.items():
        for field in MATERIAL.get(table,()):
            val=row[field]
            if val is None or (type(val) is str and val in UNKNOWN):
                continue
            minimum=3
            if table=="05_OFFERS" and field=="zero_cost_verified" and val is True:
                minimum=6
            if table=="07_COMPATIBILITY" and row["status"]=="verified":
                minimum=5
            if table=="08_ASSESSMENTS" and field=="suitability" and val=="confidential":
                minimum=5
            key=(table,rid,field)
            current=[(e,v,rd) for e,v,rd,due in evidence.get(key,[]) if due>=as_of and MIN_GRADE[e["grade"]]>=minimum]
            require(any(e["outcome"]=="supports" and equal_value(v,val) for e,v,_ in current),"missing current material evidence: "+table+"."+field)
            require(not any(e["outcome"]=="contradicts" and due>=as_of and MIN_GRADE[e["grade"]]>=3 for e,_,_,due in evidence.get(key,[])),"unresolved current contradictory material evidence")
            if minimum==6:
                require(any(e["outcome"]=="supports" and equal_value(v,val) and e["scenario"] for e,v,_ in current),"missing exact E6 scenario")
            covered+=1
        for name in ("last_reviewed","assessed_on","test_date"):
            if row.get(name) is not None:
                require(date.fromisoformat(row[name])<=as_of,"future review or test date")
        if row.get("review_due") is not None and table in {"05_OFFERS","08_ASSESSMENTS"}:
            require(date.fromisoformat(row["review_due"])>=as_of,"stale record review")
        if table=="05_OFFERS" and row["zero_cost_verified"] is True:
            require(row["availability"]=="active" and row["access"] not in {"Closed","Unverified"},"unavailable zero-cost offer")
            require(row["expiry_date"] is None or date.fromisoformat(row["expiry_date"])>=as_of,"expired zero-cost offer")
    return {"material_fields_covered":covered,"source_truth_verified":False,"release_authorized":False}

def col_number(s):
    n=0
    for c in s:n=n*26+ord(c)-64
    require(1<=n<=16384,"Excel column limit")
    return n

def col_name(n):
    out=""
    while n:
        n,r=divmod(n-1,26);out=chr(65+r)+out
    return out

def parse_cell(cell, shared):
    require(cell.find(M+"f") is None,"formula forbidden in draft workbook")
    typ=cell.get("t","n")
    require(all(c.tag in {M+"v",M+"is"} for c in cell) and len(cell)<=1,"unexpected or duplicate cell payload")
    v=cell.find(M+"v")
    if typ=="inlineStr":
        require(v is None,"ambiguous inline cell")
        x=cell.find(M+"is")
        require(x is not None,"missing inline text")
        return "".join(n.text or "" for n in x.iter(M+"t"))
    if v is None or v.text is None:
        require(typ=="n","ambiguous blank cell")
        return None
    raw=v.text
    if typ=="s":
        require(re.fullmatch(r"0|[1-9][0-9]*",raw) is not None,"invalid shared-string index")
        i=int(raw)
        require(i<len(shared),"shared-string index out of range")
        return shared[i]
    if typ=="b":
        require(raw in {"0","1"},"invalid Excel boolean")
        return raw=="1"
    require(typ=="n","unsupported cell type")
    try:
        result=int(raw) if re.fullmatch(r"-?(?:0|[1-9][0-9]*)",raw) else float(raw)
    except (ValueError,OverflowError) as exc: raise Invalid("invalid numeric cell") from exc
    require(type(result) in (int,float) and abs(result)<=1e15 and math.isfinite(result),"non-finite or nonportable numeric cell")
    return result

def rels(parts, owner):
    folder,name=owner.rsplit("/",1)
    path=folder+"/_rels/"+name+".rels"
    require(path in parts,"missing part relationships")
    out={}
    for r in parts[path]:
        rid=r.get("Id")
        target=r.get("Target","")
        require(rid not in out and target and "\\" not in target,"invalid relationship")
        stack=[] if target.startswith("/") else folder.split("/")
        for p in target.lstrip("/").split("/"):
            if p=="..":
                require(stack,"relationship escapes package");stack.pop()
            elif p!=".":
                portable_name(p);stack.append(p)
        resolved="/".join(stack)
        require(resolved in parts,"missing relationship target")
        out[rid]=(r.get("Type"),resolved)
    return out

def control_tables(schema, control, counts, filename, blank):
    """Validate exact dictionary/taxonomy inventory and initial local manifest."""
    tables={t["sheet"]:t for t in schema["tables"]}
    expected={}
    for table,t in tables.items():
        for c in t["columns"]:
            key=table+"."+c["name"]
            expected[key]={"field_id":key,"table_name":table,"column_name":c["name"],
                           "data_type":c["type"],"required":c["required"],"description":c["description"],
                           "foreign_key":t.get("foreign_keys",{}).get(c["name"])}
    seen=set()
    for row in control["02_DICTIONARY"]:
        key=row["field_id"]
        require(type(key) is str and key in expected and key not in seen,"unknown or duplicate dictionary field")
        for k,v in expected[key].items():
            require(equal_value(row[k],v),"dictionary differs from draft schema: "+key)
        if row["unit_rule"] is not None: public_text(row["unit_rule"])
        seen.add(key)
    require(seen==set(expected),"incomplete dictionary")
    expected_tax={family+":"+code:(family,code) for family,values in schema["enums"].items() for code in values}
    seen=set()
    for row in control["03_TAXONOMY"]:
        key=row["taxonomy_id"]
        require(type(key) is str and key in expected_tax and key not in seen,"unknown or duplicate taxonomy ID")
        require((row["family"],row["code"])==expected_tax[key],"taxonomy code mismatch")
        for k in ("display_label","definition"):
            require(type(row[k]) is str and bool(row[k].strip()),"missing taxonomy label/definition")
            public_text(row[k])
        require(row["deprecated"] is False and row["replacement_id"] is None,"unexpected taxonomy retirement")
        seen.add(key)
    require(seen==set(expected_tax),"incomplete taxonomy")
    seen=set();ids=set();datasets=set();editions=set()
    for row in control["01_MANIFEST"]:
        table=row["table_name"];pid=row["partition_id"];dataset=row["dataset_id"]
        require(type(table) is str and table in tables and table not in seen,"unexpected or duplicate manifest table")
        require(check_id(pid) and pid not in ids and check_id(dataset),"invalid partition/dataset ID")
        require(row["schema_version"]==schema["template_version"],"manifest schema version mismatch")
        require(type(row["relative_path"]) is str and row["relative_path"]==filename,"local workbook manifest path mismatch")
        path_parts(row["relative_path"])
        require(type(row["record_count"]) is int and row["record_count"]==counts[table],"manifest record count mismatch")
        require(row["partition_state"]=="active" and row["previous_partition_id"] is None and row["artifact_sha256"] is None,"invalid initial local partition metadata")
        if blank: require(row["data_version"] is None,"data edition in blank template")
        else: version(row["data_version"])
        editions.add(row["data_version"]);datasets.add(dataset);seen.add(table);ids.add(pid)
    require(seen==set(tables) and len(datasets)==1 and len(editions)==1,"incomplete or inconsistent manifest")
    research_ids={r for r in ids}
    require(not research_ids.intersection(datasets),"dataset ID collides with partition ID")
    return {"partition_ids":ids,"dataset_id":next(iter(datasets)),"data_version":next(iter(editions))}

def _read_partition(path,schema,*,blank):
    """Strict, macro-free canonical subset. Date fields must be ISO text.

    Table header-only is represented by a row-1 range. Actual Excel UI
    expansion/roundtrip and final formatting are separate qualification gates.
    """
    validate_design(schema)
    require(type(blank) is bool,"explicit blank/filled mode")
    require(path.suffix==".xlsx","XLSX suffix required")
    # All parsing uses one bounded byte snapshot, never reopens mutable input.
    raw=read_bytes(path,104857600)
    original=digest(raw)
    with tempfile.TemporaryDirectory() as temp:
        staged=Path(temp)/"snapshot.xlsx"
        staged.write_bytes(raw)
        require(preflight_xlsx(staged)==original,"staged workbook digest mismatch")
        with zipfile.ZipFile(staged) as z:
            parts={i.filename:ET.fromstring(z.read(i)) for i in z.infolist()}
    ct="{http://schemas.openxmlformats.org/package/2006/content-types}"
    overrides={n.get("PartName"):n.get("ContentType") for n in parts["[Content_Types].xml"] if n.tag==ct+"Override"}
    require(overrides.get("/xl/workbook.xml")=="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml","incorrect workbook content type")
    office=[n for n in parts["_rels/.rels"] if n.get("Type")==T+"officeDocument"]
    require(len(office)==1 and office[0].get("Target") in {"xl/workbook.xml","/xl/workbook.xml"},"wrong root workbook relationship")
    for root in parts.values():
        for n in root.iter():
            local=n.tag.rsplit("}",1)[-1]
            require(local not in {"f","formula","formula1","formula2","calculatedColumnFormula","totalsRowFormula","definedName","hyperlink","hyperlinks","extLst","dataValidation","conditionalFormatting"},"unsupported formula or active workbook feature")
    wb=parts["xl/workbook.xml"]
    sheets=wb.find(M+"sheets")
    require(sheets is not None and [s.get("name") for s in sheets]==schema["sheet_order"],"sheet names/order mismatch")
    wb_rels=rels(parts,"xl/workbook.xml")
    shared=[]; shared_seen=False
    for typ,target in wb_rels.values():
        if typ==T+"sharedStrings":
            require(not shared_seen,"multiple shared-string parts")
            shared_seen=True
            require(parts[target].tag==M+"sst","invalid shared strings")
            shared=["".join(n.text or "" for n in si.iter(M+"t")) for si in parts[target]]
            require(len(shared)<=MAX_ROWS*10,"shared-string limit")
    tablemap={t["sheet"]:t for t in schema["tables"]}
    data={name:[] for name in RESEARCH}
    used_parts=set();used_tables=set();used_sheet_ids=set()
    counts={}; control={t["sheet"]:[] for t in schema["tables"] if t.get("control") is True}
    table_names=set(); table_ids=set()
    for s in sheets:
        name=s.get("name");rid=s.get(R+"id");sid=s.get("sheetId")
        require(s.get("state","visible")=="visible" and sid and sid not in used_sheet_ids,"hidden or duplicate sheet")
        used_sheet_ids.add(sid)
        require(rid in wb_rels and wb_rels[rid][0]==T+"worksheet","worksheet relationship mismatch")
        part=wb_rels[rid][1]
        require(part not in used_parts,"worksheet part reused");used_parts.add(part)
        root=parts[part]
        require(overrides.get("/"+part)=="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml","incorrect worksheet content type")
        require(root.tag==M+"worksheet","worksheet root")
        for n in root.iter():
            if n.tag in {M+"row",M+"col"}: require(n.get("hidden","0") in {"0","false"},"hidden row or column")
            require(n.tag not in {M+"mergeCell",M+"mergeCells"},"merged cells forbidden")
        sd=root.find(M+"sheetData")
        require(sd is not None,"missing sheet data")
        rows=[]
        for rr in sd:
            require(rr.tag==M+"row" and rr.get("r")==str(len(rows)+1),"noncontiguous worksheet rows")
            values={}
            for c in rr:
                require(c.tag==M+"c","unexpected row element")
                match=CELL.fullmatch(c.get("r",""))
                require(match is not None and int(match.group(2))==len(rows)+1,"invalid cell address")
                column=col_number(match.group(1))
                require(column not in values,"duplicate cell address")
                values[column]=parse_cell(c,shared)
            rows.append(values)
            require(len(rows)<=MAX_ROWS+1,"draft partition row limit")
        if name=="00_README":
            require(root.find(M+"tableParts") is None,"README must not contain a research table")
            require(all(v is None or type(v) is str for row in rows for v in row.values()),"README must be literal text")
            for row in rows:
                for val in row.values():
                    if val is not None and val.strip(): public_text(val)
            continue
        headers=[c["name"] for c in tablemap[name]["columns"]]
        width=len(headers)
        require(rows and rows[0]=={i+1:h for i,h in enumerate(headers)},"exact column headers required")
        tp=root.find(M+"tableParts")
        require(tp is not None and len(tp)==1 and tp.get("count")=="1","one Excel table per worksheet required")
        tr=rels(parts,part);table_id=tp[0].get(R+"id")
        require(table_id in tr and tr[table_id][0]==T+"table","table relationship mismatch")
        target=tr[table_id][1]
        require(target not in used_tables,"table part reused");used_tables.add(target)
        table=parts[target];end=col_name(width)+str(len(rows))
        require(overrides.get("/"+target)=="application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml","incorrect table content type")
        tn=table.get("displayName","").casefold();tid=table.get("id","")
        require(tn and tn not in table_names and re.fullmatch(r"[1-9][0-9]*",tid) and tid not in table_ids,"duplicate or invalid table identity")
        table_names.add(tn);table_ids.add(tid)
        require(table.tag==M+"table" and table.get("ref")=="A1:"+end and table.get("headerRowCount","1")=="1" and table.get("totalsRowCount","0")=="0","invalid table bounds")
        tc=table.find(M+"tableColumns")
        require(tc is not None and tc.get("count")==str(width) and [c.get("name") for c in tc]==headers,"table column metadata mismatch")
        for row in rows[1:]:
            require(all(i<=width for i in row),"data outside table")
            record={h:row.get(i+1) for i,h in enumerate(headers)}
            require(any(v is not None for v in record.values()),"blank data row in table")
            if name in RESEARCH:
                require(not blank,"research data in blank workbook")
                data[name].append(record)
            else:
                control[name].append(record)
        counts[name]=len(rows)-1
    require(len(used_parts)==12 and len(used_tables)==11,"incomplete workbook inventory")
    require({n for n in parts if re.fullmatch(r"xl/worksheets/[^/]+\.xml",n)}==used_parts,"orphan worksheet")
    require({n for n in parts if re.fullmatch(r"xl/tables/[^/]+\.xml",n)}==used_tables,"orphan table")
    identity=control_tables(schema,control,counts,path.name,blank)
    return {"sha256":original,"table_rows":counts,"research":data,
            "identity":identity,"workbook_qualified":False}

def read_draft_xlsx(path,schema,*,blank):
    proof=_read_partition(path,schema,blank=blank)
    validate_records(schema,proof["research"])
    reject_control_collisions(schema,proof["research"],proof["identity"]["partition_ids"]|{proof["identity"]["dataset_id"]})
    return proof

def reject_control_collisions(schema, data, control_ids):
    ids={r[t["primary_key"]] for t in schema["tables"] if t["sheet"] in RESEARCH for r in data[t["sheet"]]}
    ids.update(r["claim_id"] for r in data["09_EVIDENCE"])
    require(not control_ids.intersection(ids),"control and research IDs collide")

def read_partitioned_library(root,schema,index_bytes,expected_index_sha,as_of):
    """Verify an independently pinned, immutable multi-XLSX edition.

    Each physical workbook has local control metadata and all 12 sheets. The
    external index is authoritative for its file inventory and global counts.
    Cross-workbook foreign keys resolve only after every member is read.
    No workbook creation, approval or publication occurs here.
    """
    validate_design(schema)
    regular(root,True)
    require(digest(index_bytes)==expected_index_sha,"external index digest mismatch")
    index=strict_json(index_bytes)
    require(type(index) is dict and set(index)=={"schema_sha256","dataset_id","data_version","files","global_counts"},"edition index shape")
    require(index["schema_sha256"]==digest(canonical(schema)),"edition schema mismatch")
    require(check_id(index["dataset_id"]),"invalid edition dataset ID")
    version(index["data_version"])
    entries=index["files"]
    require(type(entries) is list and 0<len(entries)<=128,"workbook partition count limit")
    actual=artifact_inventory(root)
    require(all(e["path"].endswith(".xlsx") and "/" not in e["path"] for e in actual),"unexpected edition file")
    require(len(actual)==len(entries),"edition inventory count mismatch")
    by_path={e["path"]:e for e in actual}
    all_rows={name:[] for name in RESEARCH}
    partition_ids=set()
    seen=set()
    total=0
    for e in entries:
        require(type(e) is dict and set(e)=={"path","sha256","size_bytes","table_rows"},"partition entry shape")
        name=e["path"]
        require(type(name) is str and name in by_path and name not in seen,"missing or duplicate partition path")
        require(type(e["size_bytes"]) is int and e["size_bytes"]==by_path[name]["size_bytes"] and e["size_bytes"]<=52428800,"partition size mismatch or limit")
        require(e["sha256"]==by_path[name]["sha256"],"partition checksum mismatch")
        proof=_read_partition(root/name,schema,blank=False)
        require(proof["sha256"]==e["sha256"],"partition changed while reading")
        require(canonical(proof["table_rows"])==canonical(e["table_rows"]),"partition table counts mismatch")
        identity=proof["identity"]
        require(identity["dataset_id"]==index["dataset_id"] and identity["data_version"]==index["data_version"],"mixed dataset or edition")
        require(not partition_ids.intersection(identity["partition_ids"]),"duplicate partition IDs")
        partition_ids.update(identity["partition_ids"])
        for k in RESEARCH:
            total+=len(proof["research"][k])
            require(total<=1000000,"edition validation budget exceeded; use a future streaming index")
            all_rows[k].extend(proof["research"][k])
        seen.add(name)
    require(seen==set(by_path),"unregistered partition")
    require(artifact_inventory(root)==actual,"edition changed during validation")
    counts=validate_records(schema,all_rows)
    require(canonical(counts)==canonical(index["global_counts"]),"global table counts mismatch")
    reject_control_collisions(schema,all_rows,partition_ids|{index["dataset_id"]})
    evidence_check(schema,all_rows,as_of)
    return {"index_sha256":expected_index_sha,"global_counts":counts,
            "partition_count":len(entries),"research":all_rows,"workbook_qualified":False}

def verify_migration(schema, snapshot, snapshot_sha, ledger, source, result, as_of):
    """Validate preserved source bytes and canonical record identity before staging."""
    validate_records(schema,source)
    validate_records(schema,result)
    offers={r["offer_id"] for r in result["05_OFFERS"]}
    counts=reconcile_sources(snapshot,snapshot_sha,ledger,offers,54)
    # This conservative initial migration must never erase existing canonical rows.
    tables={t["sheet"]:t for t in schema["tables"]}
    for table in RESEARCH:
        pk=tables[table]["primary_key"]
        dest={r[pk]:r for r in result[table]}
        for old in source[table]:
            require(old[pk] in dest and canonical(dest[old[pk]])==canonical(old),"migration altered existing record; explicit successor migration required")
    evidence_check(schema,result,as_of)
    return counts

def publish_staged_pointer(root, expected_bytes, edition_name, expected_inventory, *, inject=None):
    """Synthetic-ready atomic pointer publication in a trusted private staging root.

    Single-writer lock; old edition directories untouched. Failure before replace
    leaves the original pointer. An abandoned lock blocks further writes.
    The pointer is not a release/owner acceptance record.
    """
    regular(root,True);portable_name(edition_name)
    require(type(expected_bytes) is bytes,"expected pointer bytes required")
    pointer=root/"current.json";lock=root/".publish.lock"
    fd=None; temp=None
    try:
        fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        os.close(fd);fd=-1
        require(read_bytes(pointer,262144)==expected_bytes,"stale publication pointer")
        candidate=root/edition_name
        actual=artifact_inventory(candidate)
        require(actual==expected_inventory,"staged inventory changed")
        if inject:inject("validated")
        payload=canonical({"edition":edition_name,"inventory_sha256":digest(canonical(actual)),"release_authorized":False})
        with tempfile.NamedTemporaryFile(dir=root,prefix=".pointer-",delete=False) as f:
            temp=Path(f.name);f.write(payload);f.flush();os.fsync(f.fileno())
        if inject:inject("before_replace")
        require(read_bytes(pointer,262144)==expected_bytes,"publication pointer changed")
        require(artifact_inventory(candidate)==actual,"staged inventory changed")
        os.replace(temp,pointer);temp=None
        return payload
    finally:
        if temp is not None:temp.unlink(missing_ok=True)
        if fd is not None:
            if fd!=-1:os.close(fd)
            lock.unlink()
