import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "device_firmware_guard", ROOT / "scripts" / "device_firmware_guard.py"
)
guard = importlib.util.module_from_spec(spec)
sys.modules["device_firmware_guard"] = guard
assert spec.loader is not None
spec.loader.exec_module(guard)

REGISTRY = json.loads((ROOT / "data" / "device_manuals.json").read_text("utf-8"))


class DeviceFamilyTests(unittest.TestCase):
    def test_dr_and_de_resolve_to_dr_family(self):
        for model in ("FTM-400DR", "FTM-400DE", "ftm-400dr"):
            with self.subTest(model=model):
                self.assertEqual(
                    guard.resolve_family(model, REGISTRY)["id"],
                    "YAESU.FTM400.DR-DE",
                )

    def test_xdr_and_xde_resolve_to_xdr_family(self):
        for model in ("FTM-400XDR", "FTM-400XDE", "ftm-400xde"):
            with self.subTest(model=model):
                self.assertEqual(
                    guard.resolve_family(model, REGISTRY)["id"],
                    "YAESU.FTM400.XDR-XDE",
                )

    def test_unknown_or_ambiguous_model_rejected(self):
        for model in ("FTM-400", "FTM-500DR", "", "DR"):
            with self.subTest(model=model):
                with self.assertRaises(ValueError):
                    guard.resolve_family(model, REGISTRY)


class FirmwarePackageTests(unittest.TestCase):
    def test_dr_exp_package_never_uses_xd_firmware(self):
        result = guard.select_package("FTM-400DR", "EXP", REGISTRY)
        self.assertEqual(result["main_package"], "FTM-400D_EXP_Firmware_Update_2020_12.zip")
        self.assertNotIn("400XD_", result["main_package"])
        self.assertEqual(result["documented_targets"]["MAIN"], "3.50")

    def test_xdr_exp_package_uses_xd_firmware(self):
        result = guard.select_package("FTM-400XDR", "EXP", REGISTRY)
        self.assertEqual(result["main_package"], "FTM-400XD_EXP_Firmware_Update_2020_12.zip")
        self.assertEqual(result["documented_targets"]["MAIN"], "4.50")

    def test_all_destinations_are_explicit(self):
        for model in ("FTM-400DR", "FTM-400XDR"):
            for destination in ("USA", "AUS", "EXP"):
                with self.subTest(model=model, destination=destination):
                    result = guard.select_package(model, destination, REGISTRY)
                    self.assertEqual(result["destination"], destination)

    def test_eu_is_not_silently_aliased_to_exp(self):
        with self.assertRaises(ValueError):
            guard.select_package("FTM-400DR", "EU", REGISTRY)

    def test_country_name_is_not_used_as_destination(self):
        with self.assertRaises(ValueError):
            guard.select_package("FTM-400DR", "TURKEY", REGISTRY)

    def test_package_selection_withholds_update_steps(self):
        result = guard.select_package("FTM-400DR", "EXP", REGISTRY)
        self.assertEqual(
            result["update_instruction_status"],
            "REQUIRE_PACKAGE_FIRMWARE_UPGRADE_MANUAL",
        )
        self.assertIn("not an update procedure", result["warning"].lower())
        self.assertIsNone(result["legal_verdict"])

    def test_operating_manual_remains_pending(self):
        result = guard.select_package("FTM-400XDR", "USA", REGISTRY)
        self.assertEqual(
            result["operating_manual_content_status"],
            "pending_full_content_verification",
        )


class VersionAssessmentTests(unittest.TestCase):
    def test_dr_documented_targets_match(self):
        result = guard.assess_versions("FTM-400DR", "3.50", "4.31", REGISTRY)
        self.assertEqual(result["status"], "MATCHES_DOCUMENTED_2020_TARGETS")
        self.assertTrue(result["main_matches"])
        self.assertTrue(result["dsp_matches"])

    def test_xdr_documented_targets_match(self):
        result = guard.assess_versions("FTM-400XDR", "4.50", "4.31", REGISTRY)
        self.assertEqual(result["status"], "MATCHES_DOCUMENTED_2020_TARGETS")

    def test_mismatched_version_does_not_claim_update_direction(self):
        result = guard.assess_versions("FTM-400DR", "9.99", "4.31", REGISTRY)
        self.assertEqual(
            result["status"],
            "DOES_NOT_MATCH_DOCUMENTED_2020_TARGETS_VERIFY_BEFORE_UPDATE",
        )
        self.assertFalse(result["main_matches"])
        self.assertNotIn("older", json.dumps(result).lower())
        self.assertNotIn("newer", json.dumps(result).lower())

    def test_empty_versions_rejected(self):
        with self.assertRaises(ValueError):
            guard.assess_versions("FTM-400DR", "", "4.31", REGISTRY)
        with self.assertRaises(ValueError):
            guard.assess_versions("FTM-400DR", "3.50", "", REGISTRY)

    def test_version_assessment_has_no_legal_verdict(self):
        result = guard.assess_versions("FTM-400DR", "3.50", "4.31", REGISTRY)
        self.assertIsNone(result["legal_verdict"])


if __name__ == "__main__":
    unittest.main()
