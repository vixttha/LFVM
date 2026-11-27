import copy
from pathlib import Path
import sys
import unittest
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from foundation import Invalid
from workbook_design import load_design
from draft_records import validate_records, RESEARCH
SCHEMA=load_design(Path(__file__).resolve().parents[1]/"schemas"/"workbook-draft-v1.json")
def uid(n): return str(uuid.UUID(int=n,version=4))
def row(table,**kw):
    t=next(t for t in SCHEMA["tables"] if t["sheet"]==table)
    return {**{c["name"]:None for c in t["columns"]},**kw}
def fixture():
    d={name:[] for name in RESEARCH}
    p="04_PROVIDERS"; o="05_OFFERS"; r="06_RESOURCES"
    d[p]=[row(p,entity_id=uid(1),entity_kind="organization",name="Synthetic organization",status="unknown",first_discovered="2026-01-01"),row(p,entity_id=uid(2),entity_kind="service",parent_id=uid(1),name="Synthetic service",status="unknown",first_discovered="2026-01-01")]
    d[o]=[row(o,offer_id=uid(3),service_id=uid(2),offer_name="Synthetic offer",legacy_category="VM",free_class="F0",access="Unverified",environment="vm",availability="unknown",execution="unknown",funding="unknown",eligibility="unknown",expiration="unknown",custom_code="unknown",commercial_use="unknown",llm_use="unknown",deposit_state="unknown",setup_fee_state="unknown",recurring_fee_state="unknown",storage_fee_state="unknown",network_fee_state="unknown",overage_fee_state="unknown",renewal_fee_state="unknown",billing_cap="unknown",verification="unverified")]
    d[r]=[row(r,resource_id=uid(4),offer_id=uid(3),resource_kind="profile",profile_name="Synthetic configuration",value_state="known",guarantee="unknown"),row(r,resource_id=uid(5),offer_id=uid(3),profile_id=uid(4),resource_kind="measurement",metric="ram",value_state="known",value_min=4,unit="GiB",guarantee="typical")]
    return d
class RecordTests(unittest.TestCase):
    def reject(self,mutate):
        d=fixture();mutate(d)
        with self.assertRaises(Invalid):validate_records(SCHEMA,d)
    def test_fixture(self):self.assertEqual(validate_records(SCHEMA,fixture())["05_OFFERS"],1)
    def test_blank(self):self.assertEqual(sum(validate_records(SCHEMA,{k:[] for k in RESEARCH}).values()),0)
    def test_duplicate(self):self.reject(lambda d:d["06_RESOURCES"][0].update(resource_id=uid(3)))
    def test_dangling(self):self.reject(lambda d:d["05_OFFERS"][0].update(service_id=uid(99)))
    def test_wrong_hierarchy(self):self.reject(lambda d:d["05_OFFERS"][0].update(service_id=uid(1)))
    def test_bool_not_number(self):self.reject(lambda d:d["06_RESOURCES"][1].update(value_min=True))
    def test_zero_value(self):
        d=fixture();d["06_RESOURCES"][1]["value_min"]=0;self.assertEqual(validate_records(SCHEMA,d)["06_RESOURCES"],2)
    def test_unknown_not_zero(self):self.reject(lambda d:d["06_RESOURCES"][1].update(value_state="unknown",value_min=0))
    def test_units(self):self.reject(lambda d:d["06_RESOURCES"][1].update(unit="hours"))
    def test_range(self):self.reject(lambda d:d["06_RESOURCES"][1].update(value_max=3))
    def test_bad_expiry(self):self.reject(lambda d:d["05_OFFERS"][0].update(expiration="fixed_date"))
    def test_zero_cost_unknown(self):self.reject(lambda d:d["05_OFFERS"][0].update(zero_cost_verified=True))
    def test_invalid_date(self):self.reject(lambda d:d["04_PROVIDERS"][0].update(first_discovered="2026-02-30"))
    def test_false_is_known(self):
        d=fixture();d["05_OFFERS"][0]["zero_cost_verified"]=False;self.assertEqual(validate_records(SCHEMA,d)["05_OFFERS"],1)
    def test_field_state(self):
        d=fixture();t="10_RELATIONSHIPS";d[t]=[row(t,relationship_id=uid(6),from_table="05_OFFERS",from_id=uid(3),relation="field_state",field_name="card_required",value_state="conflicting")];self.assertEqual(validate_records(SCHEMA,d)[t],1)
        d["05_OFFERS"][0]["card_required"]=False
        with self.assertRaises(Invalid):validate_records(SCHEMA,d)
    def test_taxonomy_link(self):
        d=fixture();t="10_RELATIONSHIPS";d[t]=[row(t,relationship_id=uid(6),from_table="05_OFFERS",from_id=uid(3),relation="category",to_table="03_TAXONOMY",to_id="legacy_category:VM")];self.assertEqual(validate_records(SCHEMA,d)[t],1)
    def test_fake_verified(self):
        t="07_COMPATIBILITY"
        self.reject(lambda d:d[t].append(row(t,compatibility_id=uid(6),offer_id=uid(3),software_name="synthetic",status="verified")))
    def test_evidence_target(self):
        t="09_EVIDENCE"
        self.reject(lambda d:d[t].append(row(t,evidence_id=uid(6),claim_id=uid(7),target_table="05_OFFERS",target_id=uid(3),field_name="imaginary",claimed_value="true",retrieved_on="2026-01-01",review_due="2026-02-01",grade="E0",outcome="inconclusive")))
    def test_secret(self):self.reject(lambda d:d["05_OFFERS"][0].update(notes="ghp_"+"a"*36))
