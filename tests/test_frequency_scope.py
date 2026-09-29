import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = json.loads((ROOT / "data" / "frequency_scope.json").read_text("utf-8"))
RAW = json.loads((ROOT / "data" / "btk_amateur_table_raw.json").read_text("utf-8"))


def load_lookup():
    spec = importlib.util.spec_from_file_location(
        "frequency_scope_lookup", ROOT / "scripts" / "frequency_scope_lookup.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["frequency_scope_lookup"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lookup = load_lookup()


class FrequencyScopeTests(unittest.TestCase):
    def test_one_to_one_with_all_33_raw_rows(self):
        self.assertEqual(len(RAW["rows"]), 33)
        self.assertEqual(len(SCOPE["entries"]), 33)
        self.assertEqual(
            [e["source_row_index"] for e in SCOPE["entries"]],
            list(range(1, 34)),
        )

    def test_every_entry_is_scope_only(self):
        for entry in SCOPE["entries"]:
            self.assertEqual(entry["decision_authority"], "scope_evidence_only")
        self.assertIn(
            "never means transmission is legally allowed",
            SCOPE["scope_semantics"],
        )

    def test_c_145_is_source_listed_but_not_a_legal_verdict(self):
        result = lookup.lookup_scope(SCOPE, 145.0, "C")
        self.assertEqual(result["scope_status"], "SOURCE_LISTED")
        self.assertEqual(result["legal_status"], "UNKNOWN")
        self.assertEqual(result["permission_inference"], "PROHIBITED")
        self.assertEqual(result["matches"][0]["source_row_index"], 18)

    def test_430_to_440_gap_is_not_inferred(self):
        result = lookup.lookup_scope(SCOPE, 434.0, "C")
        self.assertEqual(result["scope_status"], "NOT_LISTED_IN_PRIMARY_RAW_SCOPE")
        self.assertEqual(result["legal_status"], "UNKNOWN")
        self.assertEqual(result["matches"], [])

    def test_visible_433_5_subband_is_listed(self):
        result = lookup.lookup_scope(SCOPE, 433.5, "C")
        self.assertEqual(result["scope_status"], "SOURCE_LISTED")
        self.assertEqual(result["matches"][0]["source_row_index"], 22)

    def test_conditional_b_7_mhz_use_is_not_promoted_to_primary_scope(self):
        result = lookup.lookup_scope(SCOPE, 7.05, "B")
        self.assertEqual(result["scope_status"], "NOT_LISTED_IN_PRIMARY_RAW_SCOPE")
        self.assertEqual(result["legal_status"], "UNKNOWN")

    def test_conflicted_b_28_mhz_condition_is_not_promoted(self):
        result = lookup.lookup_scope(SCOPE, 28.5, "B")
        self.assertEqual(result["scope_status"], "NOT_LISTED_IN_PRIMARY_RAW_SCOPE")
        self.assertEqual(result["legal_status"], "UNKNOWN")

    def test_a_28_mhz_scope_preserves_conflicts(self):
        result = lookup.lookup_scope(SCOPE, 28.5, "A")
        self.assertEqual(result["scope_status"], "SOURCE_LISTED")
        conflicts = set(result["matches"][0]["conflict_ids"])
        self.assertIn("TR-BTK-EMISSION-001", conflicts)
        self.assertIn("TR-BTK-UNIT-001", conflicts)

    def test_high_band_a_b_scope_is_preserved(self):
        result = lookup.lookup_scope(SCOPE, 136000.0, "B")
        self.assertEqual(result["scope_status"], "SOURCE_LISTED")
        self.assertEqual(result["matches"][0]["source_row_index"], 33)

    def test_absence_is_never_a_prohibition(self):
        result = lookup.lookup_scope(SCOPE, 433.0, "A")
        self.assertEqual(result["scope_status"], "NOT_LISTED_IN_PRIMARY_RAW_SCOPE")
        self.assertEqual(result["legal_status"], "UNKNOWN")
        self.assertNotEqual(result["legal_status"], "NOT_ALLOWED")


if __name__ == "__main__":
    unittest.main()
