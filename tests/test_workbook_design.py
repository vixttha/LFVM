"""Draft dictionary tests: deliberately separate from workbook acceptance."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from foundation import Invalid
from workbook_design import load_design,validate_design,SHEETS

class DesignTests(unittest.TestCase):
    def setUp(self):
        self.schema=load_design(Path(__file__).resolve().parents[1]/"schemas"/"workbook-draft-v1.json")
    def reject(self, edit):
        edit(self.schema)
        with self.assertRaises(Invalid):
            validate_design(self.schema)
    def test_layout(self):
        self.assertEqual(self.schema["sheet_order"],list(SHEETS))
        self.assertEqual(len(self.schema["tables"]),11)
    def test_reject_accepted_claim(self): self.reject(lambda s:s.update(status="accepted"))
    def test_reject_duplicate_sheet(self): self.reject(lambda s:s["sheet_order"].append("05_OFFERS"))
    def test_reject_legacy_category_rename(self): self.reject(lambda s:s["enums"]["legacy_category"].__setitem__(0,"Virtual machines"))
    def test_reject_free_class_drift(self): self.reject(lambda s:s["enums"]["free_class"].pop())
    def test_reject_duplicate_columns(self): self.reject(lambda s:s["tables"][0]["columns"].append(copy.deepcopy(s["tables"][0]["columns"][0])))
    def test_reject_unknown_type(self): self.reject(lambda s:s["tables"][0]["columns"][0].update(type="magic"))
    def test_reject_optional_key(self): self.reject(lambda s:s["tables"][0]["columns"][0].update(required=False))
    def test_reject_invalid_fk(self): self.reject(lambda s:s["tables"][4]["foreign_keys"].update(service_id="04_PROVIDERS.wrong"))
    def test_reject_missing_rules(self): self.reject(lambda s:s.pop("rules"))
    def test_reject_enum_duplicate(self): self.reject(lambda s:s["enums"]["metric"].append("ram"))
