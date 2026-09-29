import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "validate_btk_source_facts", ROOT / "scripts" / "validate_btk_source_facts.py"
)
v = importlib.util.module_from_spec(spec)
sys.modules["validate_btk_source_facts"] = v
assert spec.loader is not None
spec.loader.exec_module(v)

FACTS = json.loads((ROOT / "data" / "btk_source_facts.json").read_text("utf-8"))
RAW = json.loads((ROOT / "data" / "btk_amateur_table_raw.json").read_text("utf-8"))
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))


class BtkSourceFactTests(unittest.TestCase):
    def validate(self, facts=FACTS, raw=RAW, sources=SOURCES):
        v.validate_payloads(facts, raw, sources)

    def test_repository_source_facts_are_valid(self):
        self.validate()

    def test_all_33_rows_are_preserved(self):
        self.assertEqual(len(FACTS["rows"]), 33)
        self.assertEqual(
            [row["source_row_index"] for row in FACTS["rows"]],
            list(range(1, 34)),
        )

    def test_dual_power_rows_remain_unresolved(self):
        dual = [
            row for row in FACTS["rows"]
            if row["power_model"]["relationship"] == "SOURCE_LISTED_DUAL_VALUE_RELATION_UNRESOLVED"
        ]
        self.assertEqual(len(dual), 29)
        for row in dual:
            self.assertEqual(len(row["power_model"]["terms"]), 2)
            self.assertEqual(row["power_model"]["terms"][1]["basis"], "pep")
            self.assertEqual(row["permission_effect"], "NONE")

    def test_eirp_terms_are_not_converted_to_output_power(self):
        for index, value in ((1, 1), (2, 5), (7, 15)):
            row = FACTS["rows"][index - 1]
            self.assertEqual(row["power_model"]["relationship"], "SINGLE")
            self.assertEqual(row["power_model"]["terms"], [{
                "value": value,
                "unit": "W",
                "basis": "eirp",
                "qualifier_text": "e.i.r.p.",
            }])

    def test_condition_transcriptions_are_exactly_preserved(self):
        for raw_row, fact in zip(RAW["rows"], FACTS["rows"]):
            self.assertEqual(
                [c["transcription_text"] for c in fact["conditions"]],
                raw_row["restrictions"],
            )

    def test_repeater_beacon_and_satellite_categories_are_structured(self):
        categories = {
            c["category"]
            for row in FACTS["rows"]
            for c in row["conditions"]
        }
        self.assertIn("repeater_condition", categories)
        self.assertIn("beacon_condition", categories)
        self.assertIn("satellite_condition", categories)
        self.assertIn("emergency_cooperation", categories)

    def test_decision_effect_cannot_be_promoted(self):
        payload = copy.deepcopy(FACTS)
        payload["rows"][17]["conditions"][0]["decision_effect"] = "ALLOWED"
        with self.assertRaises(SystemExit):
            self.validate(facts=payload)

    def test_condition_text_drift_is_rejected(self):
        payload = copy.deepcopy(FACTS)
        payload["rows"][17]["conditions"][0]["transcription_text"] = "rewritten"
        with self.assertRaises(SystemExit):
            self.validate(facts=payload)

    def test_source_hash_drift_is_rejected(self):
        payload = copy.deepcopy(FACTS)
        payload["artifact_sha256"] = "sha256:" + "0" * 64
        with self.assertRaises(SystemExit):
            self.validate(facts=payload)


if __name__ == "__main__":
    unittest.main()
