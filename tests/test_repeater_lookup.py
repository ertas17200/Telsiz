import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "repeater_lookup", ROOT / "scripts" / "repeater_lookup.py"
)
lookup = importlib.util.module_from_spec(spec)
sys.modules["repeater_lookup"] = lookup
assert spec.loader is not None
spec.loader.exec_module(lookup)

REGISTRY = json.loads((ROOT / "data" / "repeaters.json").read_text("utf-8"))


class RepeaterLookupTests(unittest.TestCase):
    def test_snapshot_is_explicitly_partial(self):
        self.assertEqual(REGISTRY["coverage_status"], "partial_snapshot")
        self.assertIn("Absence", REGISTRY["coverage_note"])

    def test_kadikoy_lookup_returns_vhf_and_uhf(self):
        result = lookup.search_repeaters(branch="kadıköy", registry=REGISTRY)
        self.assertGreaterEqual(len(result["results"]), 2)
        self.assertEqual({r["band"] for r in result["results"]}, {"VHF", "UHF"})

    def test_turkish_search_normalization_accepts_ascii_i_and_diacritic_free_text(self):
        result = lookup.search_repeaters(branch="kadikoy", site="kayisdagi", registry=REGISTRY)
        self.assertGreaterEqual(len(result["results"]), 2)

    def test_band_filter(self):
        result = lookup.search_repeaters(branch="KOCAELİ", band="UHF", registry=REGISTRY)
        self.assertTrue(result["results"])
        self.assertTrue(all(r["band"] == "UHF" for r in result["results"]))

    def test_maintenance_status_is_preserved(self):
        result = lookup.search_repeaters(site="KURTTEPE", registry=REGISTRY)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["operational_status"], "Bakımda")

    def test_association_status_never_becomes_official_permission(self):
        result = lookup.search_repeaters(registry=REGISTRY)
        for record in result["results"]:
            self.assertEqual(record["official_permission_status"], "UNKNOWN_NOT_VERIFIED")
            self.assertIsNone(record["legal_verdict"])
        self.assertIsNone(result["legal_verdict"])

    def test_empty_search_does_not_mean_nonexistence(self):
        result = lookup.search_repeaters(site="DOES-NOT-EXIST", registry=REGISTRY)
        self.assertEqual(result["results"], [])
        self.assertEqual(result["coverage_status"], "partial_snapshot")
        self.assertIn("Absence", result["coverage_note"])

    def test_invalid_band_rejected(self):
        with self.assertRaises(ValueError):
            lookup.search_repeaters(band="HF", registry=REGISTRY)

    def test_snapshot_fresh_for_30_days_inclusive(self):
        result = lookup.snapshot_freshness("2026-10-28T22:12:00Z", REGISTRY)
        self.assertEqual(result["status"], "FRESH")

    def test_snapshot_stale_after_policy_threshold(self):
        result = lookup.snapshot_freshness("2026-10-29T22:12:01Z", REGISTRY)
        self.assertEqual(result["status"], "STALE")

    def test_future_snapshot_reference_rejected(self):
        with self.assertRaises(ValueError):
            lookup.snapshot_freshness("2026-09-28T22:11:59Z", REGISTRY)

    def test_freshness_policy_is_repo_policy(self):
        result = lookup.snapshot_freshness("2026-09-28T22:12:00Z", REGISTRY)
        self.assertIn("repository", result["policy_origin"].lower())


if __name__ == "__main__":
    unittest.main()
