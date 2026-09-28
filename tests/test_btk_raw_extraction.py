import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location("validate_btk_raw", ROOT / "scripts" / "validate_btk_raw.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_btk_raw"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


v = load_module()
RAW = json.loads((ROOT / "data" / "btk_amateur_table_raw.json").read_text("utf-8"))
EMISSIONS = json.loads((ROOT / "data" / "btk_emission_types.json").read_text("utf-8"))
SEMANTIC = json.loads((ROOT / "data" / "frequency_table.json").read_text("utf-8"))


class RawBtkExtractionTests(unittest.TestCase):
    def test_repository_raw_transcription_is_valid(self):
        v.validate_payloads(RAW, EMISSIONS)

    def test_exact_source_row_count_is_33(self):
        self.assertEqual(len(RAW["rows"]), 33)
        self.assertEqual(RAW["source_rows_counted"], 33)

    def test_emission_definition_count_is_24(self):
        self.assertEqual(len(EMISSIONS["definitions"]), 24)

    def test_undefined_source_emission_codes_are_preserved_not_normalized(self):
        raw_codes = {c for row in RAW["rows"] for c in row["emission_codes"]}
        defined = {d["code"] for d in EMISSIONS["definitions"]}
        for code in ("A3J", "J2C"):
            self.assertIn(code, raw_codes)
            self.assertNotIn(code, defined)
        self.assertIn("TR-BTK-EMISSION-001", RAW["known_source_conflicts"])

    def test_source_repetitions_are_de_duplicated_in_machine_row(self):
        row = next(r for r in RAW["rows"] if r["source_row_index"] == 16)
        self.assertEqual(len(row["emission_codes"]), len(set(row["emission_codes"])))
        self.assertIn("repeats F2B and J3F", row["notes"])

    def test_source_unit_typo_is_preserved_as_conflict(self):
        row = next(r for r in RAW["rows"] if r["frequency_min"] == 28000 and r["unit"] == "kHz")
        self.assertTrue(any("28000-29700 MHz" in x for x in row["restrictions"]))
        self.assertIn("TR-BTK-UNIT-001", RAW["known_source_conflicts"])

    def test_144_c_class_5w_condition_present(self):
        row = next(r for r in RAW["rows"] if r["frequency_min"] == 144 and r["unit"] == "MHz")
        self.assertEqual(set(row["license_classes"]), {"A", "B", "C"})
        self.assertTrue(any("C-class" in x and "5 W" in x for x in row["restrictions"]))

    def test_430_repeater_subbands_preserved(self):
        repeater_ranges = {
            (r["frequency_min"], r["frequency_max"])
            for r in RAW["rows"]
            if any("repeaters installed" in x for x in r["restrictions"])
        }
        self.assertIn((431.55, 431.825), repeater_ranges)
        self.assertIn((439.15, 439.425), repeater_ranges)

    def test_semantic_table_remains_partial(self):
        self.assertEqual(SEMANTIC["coverage_status"], "partial")
        self.assertIsNone(RAW["artifact_sha256"])
        self.assertEqual(RAW["semantic_promotion_status"], "HOLD_ARTIFACT_HASH_AND_SOURCE_CONFLICTS")

    def test_missing_raw_row_fails(self):
        raw = copy.deepcopy(RAW)
        raw["rows"].pop()
        with self.assertRaises(SystemExit):
            v.validate_payloads(raw, EMISSIONS)

    def test_duplicate_raw_range_fails(self):
        raw = copy.deepcopy(RAW)
        raw["rows"][1]["frequency_min"] = raw["rows"][0]["frequency_min"]
        raw["rows"][1]["frequency_max"] = raw["rows"][0]["frequency_max"]
        raw["rows"][1]["unit"] = raw["rows"][0]["unit"]
        with self.assertRaises(SystemExit):
            v.validate_payloads(raw, EMISSIONS)

    def test_unknown_emission_beyond_known_j2c_fails(self):
        raw = copy.deepcopy(RAW)
        raw["rows"][0]["emission_codes"].append("ZZZ")
        with self.assertRaises(SystemExit):
            v.validate_payloads(raw, EMISSIONS)


if __name__ == "__main__":
    unittest.main()
