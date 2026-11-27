"""Structural validation for an unapproved workbook design; no workbook creation."""
from __future__ import annotations
from pathlib import Path
import re
from foundation import strict_json, require, Invalid

SHEETS = ("00_README","01_MANIFEST","02_DICTIONARY","03_TAXONOMY","04_PROVIDERS","05_OFFERS","06_RESOURCES","07_COMPATIBILITY","08_ASSESSMENTS","09_EVIDENCE","10_RELATIONSHIPS","11_HISTORY")
LEGACY = ["VM","GPU notebook","Dev workspace","CI runner","Container","Serverless","Research","API only","Other"]
TYPES = {"id","text","path","version","integer","number","boolean","date","url","sha256","currency"}
NAME = re.compile(r"[a-z][a-z0-9_]*\Z")
def validate_design(schema):
    require(type(schema) is dict and schema.get("contract_version") == 1 and type(schema.get("contract_version")) is int, "draft version")
    require(schema.get("template_version") == "v0.0.0.1" and schema.get("status") == "draft_unapproved", "draft only")
    require(schema.get("sheet_order") == list(SHEETS), "sheet order")
    enums = schema.get("enums")
    require(type(enums) is dict and enums.get("legacy_category") == LEGACY, "legacy taxonomy")
    for name, values in enums.items():
        require(type(name) is str and NAME.fullmatch(name) and type(values) is list and values and all(type(x) is str and x for x in values) and len(values) == len(set(values)), "enum invalid")
    for name, expected in {"free_class":["F0","F1","F2","F3","F4","F5"],"trust":["A","B","C","U"],"access":["Public","Approval","Restricted","Closed","Unverified"],"billing_risk":["R0","R1","R2","R3","R4","RU"],"evidence_grade":["E0","E1","E2","E3","E4","E5","E6"]}.items():
        require(enums.get(name) == expected, "legacy classification drift")
    tables = schema.get("tables")
    require(type(tables) is list and all(type(t) is dict for t in tables) and [t.get("sheet") for t in tables] == list(SHEETS[1:]), "table order")
    by_sheet = {t["sheet"]:t for t in tables}
    for table in tables:
        columns = table.get("columns")
        require(type(columns) is list and columns and all(type(c) is dict for c in columns), "columns missing")
        names = [c.get("name") for c in columns]
        require(all(type(n) is str and NAME.fullmatch(n) for n in names) and len(names)==len(set(names)), "column names")
        fields = {c["name"]:c for c in columns}
        key=table.get("primary_key")
        require(type(key) is str and key in fields and fields[key].get("required") is True, "required primary key")
        for c in columns:
            typ=c.get("type")
            require(set(c)=={"name","type","required","description"} and type(typ) is str and type(c["required"]) is bool and type(c["description"]) is str and c["description"].strip(), "field specification")
            require(typ in TYPES or (typ.startswith("enum:") and typ[5:] in enums), "unsupported field type")
        for name,target in table.get("foreign_keys",{}).items():
            require(name in fields and type(target) is str and target.count(".")==1,"foreign key field")
            target_sheet,target_key=target.split(".")
            require(target_sheet in by_sheet and by_sheet[target_sheet]["primary_key"]==target_key,"foreign key target")
            target_column=next(c for c in by_sheet[target_sheet]["columns"] if c["name"]==target_key)
            require(target_column["type"]==fields[name]["type"],"foreign key type")
    require(sum(t.get("control") is True for t in tables)==3,"control table count")
    require(all(type(schema.get(k)) is dict and schema[k] for k in ("rules","missing_values","readme")),"missing design rules")
    require(type(schema.get("metric_units")) is dict and set(schema["metric_units"])==set(enums["metric"]), "metric unit inventory")
    require(all(type(v) is list and v and set(v)<=set(enums["unit"]) and len(v)==len(set(v)) for v in schema["metric_units"].values()), "metric unit rule")
    return schema

def load_design(path):
    return validate_design(strict_json(path.read_bytes()))
