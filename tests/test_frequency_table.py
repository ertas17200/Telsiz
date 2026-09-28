import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


vk = load_module("validate_knowledge")
fl = load_module("frequency_lookup")

SOURCES = {s["id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))["sources"]}
RULES = {r["id"]: r for r in json.loads((ROOT / "data" / "rules.json").read_text("utf-8"))["rules"]}
TABLE = json.loads((ROOT / "data" / "frequency_table.json").read_text("utf-8"))


class FrequencyTableValidationTests(unittest.TestCase):
    def validate(self, table, sources=None):
        vk.validate_frequency_table(table, sources or SOURCES, RULES)

    def test_repository_table_is_valid(self):
        self.validate(TABLE)

    def test_complete_coverage_rejected_without_source_hash(self):
        table = copy.deepcopy(TABLE)
        table["coverage_status"] = "complete"
        table["coverage_blocker"] = None
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_partial_coverage_requires_blocker(self):
        table = copy.deepcopy(TABLE)
        table["coverage_blocker"] = None
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_verified_row_rejects_pending_source(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0]["source_id"] = "TR.BTK.EHK.5809"
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_verified_row_rejects_amateur_association_source(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0]["source_id"] = "IARU.R1.BANDPLANS"
        with self.assertRaises(SystemExit):
            self.validate(table)

    def test_row_must_agree_with_source_rule(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0]["maximum_output_power"] = 50
        with self.assertRaises(SystemExit):
            self.validate(table)


class FrequencyLookupFailClosedTests(unittest.TestCase):
    def test_c_class_145_mhz_returns_5w_but_not_legal_verdict(self):
        result = fl.lookup(TABLE, 145.0, "C")
        self.assertEqual(result["status"], "PARTIAL_MATCH_UNDETERMINED")
        self.assertIsNone(result["legal_to_transmit"])
        self.assertEqual(result["maximum_output_power"], [(5, "W")])
        self.assertIn("emission", result["missing_dimensions"])

    def test_c_class_433_mhz_returns_5w(self):
        result = fl.lookup(TABLE, 433.0, "C")
        self.assertEqual(result["rows"], ["TR.FTM.AMATEUR.ROW.C.430-440"])
        self.assertEqual(result["maximum_output_power"], [(5, "W")])
        self.assertIsNone(result["legal_to_transmit"])

    def test_unextracted_band_is_unknown_not_forbidden(self):
        result = fl.lookup(TABLE, 14.2, "A")
        self.assertEqual(result["status"], "UNKNOWN_NOT_EXTRACTED")
        self.assertIsNone(result["legal_to_transmit"])

    def test_b_class_not_inferred_from_c_rows(self):
        result = fl.lookup(TABLE, 145.0, "B")
        self.assertEqual(result["status"], "UNKNOWN_NOT_EXTRACTED")

    def test_complete_table_with_missing_dimensions_is_still_undetermined(self):
        table = copy.deepcopy(TABLE)
        table["coverage_status"] = "complete"
        result = fl.lookup(table, 145.0, "C")
        self.assertIsNone(result["legal_to_transmit"])


if __name__ == "__main__":
    unittest.main()
