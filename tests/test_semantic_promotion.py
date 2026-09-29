import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "validate_semantic_promotion", ROOT / "scripts" / "validate_semantic_promotion.py"
)
v = importlib.util.module_from_spec(spec)
sys.modules["validate_semantic_promotion"] = v
assert spec.loader is not None
spec.loader.exec_module(v)

PROMOTION = json.loads((ROOT / "data" / "btk_semantic_promotion.json").read_text("utf-8"))
RAW = json.loads((ROOT / "data" / "btk_amateur_table_raw.json").read_text("utf-8"))
TABLE = json.loads((ROOT / "data" / "frequency_table.json").read_text("utf-8"))
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))
ARTIFACTS = json.loads((ROOT / "data" / "artifacts.json").read_text("utf-8"))


class SemanticPromotionTests(unittest.TestCase):
    def validate(self, promotion=PROMOTION, raw=RAW, table=TABLE, sources=SOURCES, artifacts=ARTIFACTS):
        v.validate_payloads(promotion, raw, table, sources, artifacts)

    def test_repository_promotion_map_is_valid(self):
        self.validate()

    def test_all_33_rows_are_mapped_once(self):
        self.assertEqual(PROMOTION["summary"]["rows_mapped"], 33)
        self.assertEqual(
            [x["source_row_index"] for x in PROMOTION["rows"]],
            list(range(1, 34)),
        )

    def test_partial_promotion_count_is_eleven(self):
        self.assertEqual(PROMOTION["summary"]["rows_with_partial_semantic_promotion"], 11)
        self.assertEqual(PROMOTION["summary"]["rows_not_ready_current_schema"], 22)

    def test_row_17_is_limited_promotion_only(self):
        mapped = PROMOTION["rows"][16]
        self.assertEqual(mapped["source_row_index"], 17)
        self.assertEqual(mapped["overall_status"], "PARTIAL_PROMOTION_PRESENT")
        self.assertEqual(mapped["current_semantic_row_ids"], ["TR.FTM.AMATEUR.ROW.AB.50-52"])
        self.assertIn("TR-BTK-EMISSION-001", mapped["blockers"])
        row = next(x for x in TABLE["rows"] if x["id"] == "TR.FTM.AMATEUR.ROW.AB.50-52")
        self.assertEqual(set(row["license_class"]), {"A", "B"})
        self.assertEqual(row["maximum_output_power"], 100)
        self.assertIsNone(row["emission"])
        self.assertIsNone(row["beacon"])

    def test_row_16_preserves_unit_conflict_blocker(self):
        mapped = PROMOTION["rows"][15]
        self.assertIn("TR-BTK-UNIT-001", mapped["blockers"])
        self.assertEqual(mapped["field_readiness"]["emissions"], "BLOCKED_SOURCE_CONFLICT")

    def test_undefined_emissions_are_blocked_not_substituted(self):
        row5 = PROMOTION["rows"][4]
        self.assertEqual(row5["emission_conflict_codes"], ["A3J"])
        self.assertEqual(row5["field_readiness"]["emissions"], "BLOCKED_SOURCE_CONFLICT")
        row17 = PROMOTION["rows"][16]
        self.assertEqual(row17["emission_conflict_codes"], ["A3J", "J2C"])

    def test_eirp_rows_are_promoted_on_eirp_basis_only(self):
        expected = {1: ("TR.FTM.AMATEUR.ROW.A.135.7-137.8-KHZ", 1), 2: ("TR.FTM.AMATEUR.ROW.A.472-479-KHZ", 5),
                    7: ("TR.FTM.AMATEUR.ROW.A.5351.5-5366.5-KHZ", 15)}
        for index, (row_id, watts) in expected.items():
            with self.subTest(index=index):
                mapped = PROMOTION["rows"][index - 1]
                self.assertEqual(mapped["field_readiness"]["power"], "PROMOTABLE_EIRP_W")
                self.assertNotIn("SEMANTIC_POWER_BASIS_MODEL_GAP", mapped["blockers"])
                self.assertEqual(mapped["current_semantic_row_ids"], [row_id])
                row = next(x for x in TABLE["rows"] if x["id"] == row_id)
                self.assertEqual(row["power_basis"], "eirp")
                self.assertEqual(row["maximum_output_power"], watts)
                self.assertEqual(row["license_class"], ["A"])
                self.assertIsNone(row["emission"])

    def test_row_7_eirp_promotion_keeps_emission_conflict(self):
        mapped = PROMOTION["rows"][6]
        self.assertEqual(mapped["blockers"], ["TR-BTK-EMISSION-001"])
        self.assertEqual(mapped["field_readiness"]["emissions"], "BLOCKED_SOURCE_CONFLICT")

    def test_eirp_readiness_cannot_be_downgraded_silently(self):
        payload = copy.deepcopy(PROMOTION)
        payload["rows"][0]["field_readiness"]["power"] = "NEEDS_POWER_BASIS_MODEL"
        with self.assertRaises(SystemExit):
            self.validate(promotion=payload)

    def test_dual_power_rows_require_multivalue_model(self):
        for index in (3, 10, 18, 25, 33):
            with self.subTest(index=index):
                mapped = PROMOTION["rows"][index - 1]
                self.assertEqual(mapped["field_readiness"]["power"], "NEEDS_MULTIVALUE_POWER_MODEL")

    def test_map_cannot_claim_permission(self):
        payload = copy.deepcopy(PROMOTION)
        payload["policy"]["does_not_create_permission"] = False
        with self.assertRaises(SystemExit):
            self.validate(promotion=payload)

    def test_artifact_hash_drift_fails(self):
        payload = copy.deepcopy(PROMOTION)
        payload["artifact_sha256"] = "sha256:" + "0" * 64
        with self.assertRaises(SystemExit):
            self.validate(promotion=payload)

    def test_semantic_row_reference_drift_fails(self):
        payload = copy.deepcopy(PROMOTION)
        payload["rows"][16]["current_semantic_row_ids"] = []
        with self.assertRaises(SystemExit):
            self.validate(promotion=payload)


if __name__ == "__main__":
    unittest.main()
