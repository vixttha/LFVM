"""Validate draft in-memory research rows; never authorizes a workbook release."""
from __future__ import annotations
from datetime import date
import math
import re
import uuid

from foundation import require, strict_json, version, Invalid
from qualification import public_url, public_text

UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
RESEARCH = ("04_PROVIDERS","05_OFFERS","06_RESOURCES","07_COMPATIBILITY","08_ASSESSMENTS","09_EVIDENCE","10_RELATIONSHIPS","11_HISTORY")
def check_id(value):
    return type(value) is str and UUID.fullmatch(value) is not None
def scalar(value, typ, enums):
    if typ.startswith("enum:"):
        require(type(value) is str and value in enums[typ[5:]], "invalid enum value")
    elif typ == "id":
        require(check_id(value), "invalid UUID v4")
    elif typ == "boolean":
        require(type(value) is bool, "invalid boolean")
    elif typ == "integer":
        require(type(value) is int, "invalid integer")
    elif typ == "number":
        require(type(value) in (int,float) and math.isfinite(value), "invalid finite number")
    elif typ == "date":
        require(type(value) is str and re.fullmatch(r"\d{4}-\d\d-\d\d",value), "invalid date format")
        try: date.fromisoformat(value)
        except ValueError as e: raise Invalid("invalid date") from e
    elif typ == "version":
        version(value)
    elif typ == "url":
        require(type(value) is str, "invalid URL value")
        public_url(value)
    elif typ == "currency":
        require(type(value) is str and re.fullmatch(r"[A-Z]{3}",value), "invalid currency syntax")
    elif typ == "text":
        require(type(value) is str and bool(value.strip()), "invalid text")
        public_text(value)
    else:
        raise Invalid("unsupported research type")

def validate_records(schema, data):
    """Rows must be fully expanded to all exact headers; null represents an empty cell."""
    require(type(data) is dict and set(data)==set(RESEARCH), "research table inventory")
    tables={t["sheet"]:t for t in schema["tables"] if t["sheet"] in RESEARCH}
    enums=schema["enums"]
    by={}; global_ids=set()
    for name in RESEARCH:
        t=tables[name]; rows=data[name]
        require(type(rows) is list, "rows must be a list")
        columns={c["name"]:c for c in t["columns"]}
        pk=t["primary_key"]
        by[name]={}
        for row in rows:
            require(type(row) is dict and set(row)==set(columns), "row headers mismatch")
            for key,c in columns.items():
                val=row[key]
                if val is None:
                    require(not c["required"], "required cell missing")
                else:
                    scalar(val,c["type"],enums)
            rid=row[pk]
            require(rid not in global_ids, "duplicate global record ID")
            global_ids.add(rid); by[name][rid]=row
    def lookup(table,rid):
        require(table in by and rid in by[table], "missing foreign key")
        return by[table][rid]
    def field(table,rid,field_name):
        target=lookup(table,rid)
        require(field_name in target, "unknown target field")
        return target
    for name, rows in by.items():
        for r in rows.values():
            for col,target in tables[name].get("foreign_keys",{}).items():
                if r[col] is not None:
                    lookup(target.split(".")[0],r[col])
    for r in by["04_PROVIDERS"].values():
        kind=r["entity_kind"]; parent=r["parent_id"]
        if kind=="organization":
            require(parent is None,"organization has parent")
        else:
            require(parent is not None,"entity has no parent")
            expected="organization" if kind=="platform" else None
            p=lookup("04_PROVIDERS",parent)
            require(p["entity_kind"]==expected if expected else p["entity_kind"] in {"organization","platform"},"invalid entity hierarchy")
    for r in by["05_OFFERS"].values():
        require(lookup("04_PROVIDERS",r["service_id"])["entity_kind"]=="service","offer requires service")
        expiry=r["expiration"]
        if expiry=="fixed_date":
            require(r["expiry_date"] is not None and r["duration_count"] is None and r["duration_unit"] is None,"invalid fixed date")
        elif expiry=="fixed_duration":
            require(r["expiry_date"] is None and r["duration_count"] is not None and r["duration_count"]>0 and r["duration_unit"] not in {None,"none","lifetime"},"invalid fixed duration")
        else:
            require(all(r[k] is None for k in ("expiry_date","duration_count","duration_unit")),"unexpected expiry fields")
        if r["permanent_free"] is True:
            require(r["expiration"] in {"none","rolling_quota"} and r["funding"] in {"recurring_allowance","renewable_credits","sponsorship"},"inconsistent permanence")
        if r["last_reviewed"] is not None and r["review_due"] is not None:
            require(r["review_due"]>=r["last_reviewed"],"offer review order")
    for r in by["06_RESOURCES"].values():
        kind=r["resource_kind"]; profile=r["profile_id"]
        values=("metric","value_min","value_max","value_text","unit","period_count","period_unit")
        if kind=="profile":
            require(profile is None and r["profile_name"] is not None and all(r[k] is None for k in values),"invalid profile")
            continue
        require(profile is not None and r["profile_name"] is None,"measurement missing profile")
        p=lookup("06_RESOURCES",profile)
        require(p["resource_kind"]=="profile" and p["offer_id"]==r["offer_id"],"cross-offer profile")
        metric=r["metric"]
        require(metric in schema["metric_units"],"metric required")
        if r["value_state"]=="known":
            require(r["unit"] in schema["metric_units"][metric],"incompatible metric unit")
            if r["unit"] in {"text","boolean"}:
                require(r["value_text"] is not None and r["value_min"] is None and r["value_max"] is None,"invalid textual measurement")
                if r["unit"]=="boolean": require(r["value_text"] in {"true","false"},"invalid resource boolean")
            else:
                require(r["value_text"] is None and r["value_min"] is not None and r["value_min"]>=0,"invalid numeric measurement")
                require(r["value_max"] is None or r["value_max"]>=r["value_min"],"invalid range")
                if r["unit"]=="count": require(type(r["value_min"]) is int and (r["value_max"] is None or type(r["value_max"]) is int),"fractional count")
        else:
            require(all(r[k] is None for k in ("value_min","value_max","value_text","unit")),"missing-state value present")
        if kind=="quota":
            require(r["period_count"] is not None and r["period_count"]>0 and r["period_unit"] not in {None,"none"},"quota period required")
        else:
            require(r["period_count"] is None and r["period_unit"] is None,"measurement has quota period")
    for r in by["07_COMPATIBILITY"].values():
        if r["profile_id"] is not None:
            p=lookup("06_RESOURCES",r["profile_id"])
            require(p["resource_kind"]=="profile" and p["offer_id"]==r["offer_id"],"compatibility profile mismatch")
        if r["status"]=="verified":
            require(r["test_date"] is not None,"verified requires test date")
        else:
            require(r["test_date"] is None and r["benchmark_value"] is None,"unverified test result")
        metric_fields=[r[k] is not None for k in ("benchmark_metric","benchmark_value","benchmark_unit")]
        require(all(metric_fields) or not any(metric_fields),"incomplete benchmark")
    dimensions={"legitimacy":"trust_grade","billing":"billing_risk","security":"risk","privacy":"risk","reliability":"risk","data_sensitivity":"suitability"}
    for r in by["08_ASSESSMENTS"].values():
        require(r["target_table"] in {"04_PROVIDERS","05_OFFERS"},"assessment target kind")
        lookup(r["target_table"],r["target_id"])
        expected=dimensions[r["dimension"]]
        require(all((r[k] is not None)==(k==expected) for k in {"trust_grade","billing_risk","risk","suitability"}),"mixed assessment dimensions")
        require(r["review_due"]>=r["assessed_on"],"assessment review order")
    claims={}; evidence=[]
    for r in by["09_EVIDENCE"].values():
        require(r["target_table"] in RESEARCH[:5],"invalid evidence target")
        field(r["target_table"],r["target_id"],r["field_name"])
        identity=(r["target_table"],r["target_id"],r["field_name"])
        require(r["claim_id"] not in global_ids,"claim identity collision")
        require(r["claim_id"] not in claims or claims[r["claim_id"]]==identity,"claim identity conflict")
        claims[r["claim_id"]]=identity
        val=strict_json(r["claimed_value"].encode("utf-8"))
        require(r["grade"]=="E0" or r["source_url"] is not None,"evidence source required")
        require(r["review_due"]>=r["retrieved_on"],"evidence review order")
        evidence.append((r,val))
    states=set()
    taxonomy={f"{family}:{value}" for family,values in enums.items() for value in values}
    for r in by["10_RELATIONSHIPS"].values():
        source=lookup(r["from_table"],r["from_id"])
        relation=r["relation"]
        if relation=="field_state":
            require(r["field_name"] in source and source[r["field_name"]] is None and r["value_state"] in {"not_applicable","conflicting"},"invalid field state")
            require(all(r[k] is None for k in ("to_table","to_id","literal_value")),"field-state target fields")
            k=(r["from_table"],r["from_id"],r["field_name"])
            require(k not in states,"duplicate field state")
            states.add(k)
        else:
            require(r["field_name"] is None and r["value_state"] is None,"unexpected field-state fields")
            if relation=="category":
                require(r["to_table"]=="03_TAXONOMY" and r["to_id"] in taxonomy and r["literal_value"] is None,"invalid taxonomy relation")
            elif relation in {"tag","alias","source_mapping"}:
                require(r["to_table"] is None and r["to_id"] is None and r["literal_value"] is not None,"invalid literal relation")
            else:
                require(r["to_table"] is not None and r["to_id"] is not None and r["literal_value"] is None,"invalid record relation")
                lookup(r["to_table"],r["to_id"])
    for r in by["11_HISTORY"].values():
        # Withdrawn historical targets remain as retained canonical rows.
        target=lookup(r["target_table"],r["target_id"])
        require(r["field_name"] is None or r["field_name"] in target,"unknown history field")
        for key in ("before_json","after_json"):
            if r[key] is not None: strict_json(r[key].encode("utf-8"))
    for r in by["05_OFFERS"].values():
        if r["zero_cost_verified"] is True:
            fees=("deposit_state","setup_fee_state","recurring_fee_state","storage_fee_state","network_fee_state","overage_fee_state","renewal_fee_state")
            require(all(r[k] in {"zero","not_applicable"} for k in fees) and r["auto_upgrade"] is False and r["billing_cap"]=="hard_zero","unbounded zero-cost claim")
            require(r["verification"]=="tested" and r["last_reviewed"] is not None and r["review_due"] is not None,"unreviewed zero-cost claim")
            require(any(e["target_table"]=="05_OFFERS" and e["target_id"]==r["offer_id"] and e["field_name"]=="zero_cost_verified" and e["grade"]=="E6" and e["outcome"]=="supports" and val is True and e["scenario"] and e["review_due"]>=r["last_reviewed"] for e,val in evidence),"zero-cost E6 scenario evidence missing")
    return {name:len(by[name]) for name in RESEARCH}
