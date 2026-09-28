import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "rf_wavelength", ROOT / "scripts" / "rf_wavelength.py"
)
rf = importlib.util.module_from_spec(spec)
sys.modules["rf_wavelength"] = rf
assert spec.loader is not None
spec.loader.exec_module(rf)

CONTRACT = json.loads((ROOT / "data" / "rf_calculator_contract.json").read_text("utf-8"))


class RfWavelengthTests(unittest.TestCase):
    def test_one_mhz_exact_free_space_wavelength(self):
        result = rf.calculate("1", "MHz", contract=CONTRACT)
        self.assertAlmostEqual(result["free_space_wavelength_m"], 299.792458, places=9)

    def test_100_mhz_quarter_and_half_wave(self):
        result = rf.calculate("100", "MHz", contract=CONTRACT)
        self.assertAlmostEqual(result["free_space_wavelength_m"], 2.99792458, places=10)
        self.assertAlmostEqual(result["quarter_wave_m"], 0.749481145, places=10)
        self.assertAlmostEqual(result["half_wave_m"], 1.49896229, places=10)

    def test_velocity_factor_scales_electrical_length(self):
        result = rf.calculate("100", "MHz", "0.66", CONTRACT)
        self.assertAlmostEqual(
            result["propagation_wavelength_m"],
            result["free_space_wavelength_m"] * 0.66,
            places=12,
        )
        self.assertAlmostEqual(
            result["quarter_wave_m"],
            result["propagation_wavelength_m"] / 4,
            places=12,
        )

    def test_unit_conversions_match(self):
        mhz = rf.calculate("145.5", "MHz", contract=CONTRACT)
        khz = rf.calculate("145500", "kHz", contract=CONTRACT)
        hz = rf.calculate("145500000", "Hz", contract=CONTRACT)
        self.assertAlmostEqual(mhz["free_space_wavelength_m"], khz["free_space_wavelength_m"], places=12)
        self.assertAlmostEqual(mhz["free_space_wavelength_m"], hz["free_space_wavelength_m"], places=12)

    def test_ghz_supported(self):
        result = rf.calculate("2.4", "GHz", contract=CONTRACT)
        self.assertAlmostEqual(result["frequency_hz"], 2_400_000_000, places=2)

    def test_nonpositive_frequency_rejected(self):
        for value in (0, -1, "0", "-3"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    rf.calculate(value, "MHz", contract=CONTRACT)

    def test_nonfinite_frequency_rejected(self):
        for value in ("NaN", "Infinity", float("inf"), float("nan")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    rf.calculate(value, "MHz", contract=CONTRACT)

    def test_boolean_frequency_rejected(self):
        with self.assertRaises(ValueError):
            rf.calculate(True, "MHz", contract=CONTRACT)

    def test_invalid_unit_rejected(self):
        with self.assertRaises(ValueError):
            rf.calculate("100", "THz", contract=CONTRACT)

    def test_invalid_velocity_factor_rejected(self):
        for value in (0, -0.1, 1.01, "NaN", True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    rf.calculate("100", "MHz", value, CONTRACT)

    def test_free_space_velocity_factor_is_one(self):
        result = rf.calculate("10", "MHz", contract=CONTRACT)
        self.assertEqual(result["velocity_factor"], 1.0)
        self.assertEqual(result["free_space_wavelength_m"], result["propagation_wavelength_m"])

    def test_output_has_no_legal_verdict(self):
        result = rf.calculate("145", "MHz", contract=CONTRACT)
        self.assertIsNone(result["legal_verdict"])
        self.assertEqual(result["source_id"], "BIPM.SI.DEFINING_CONSTANTS")

    def test_assumption_rejects_cut_length_claim(self):
        result = rf.calculate("145", "MHz", contract=CONTRACT)
        text = " ".join(result["assumptions"]).lower()
        self.assertIn("not guaranteed physical resonant antenna cut lengths", text)


if __name__ == "__main__":
    unittest.main()
