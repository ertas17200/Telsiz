import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "qcode_rst_trainer", ROOT / "scripts" / "qcode_rst_trainer.py"
)
trainer = importlib.util.module_from_spec(spec)
sys.modules["qcode_rst_trainer"] = trainer
assert spec.loader is not None
spec.loader.exec_module(trainer)

Q_DATA = json.loads((ROOT / "data" / "q_codes.json").read_text("utf-8"))


class QCodeTrainerTests(unittest.TestCase):
    def test_exact_qcode_subset(self):
        expected = {
            "QRG", "QRK", "QRL", "QRM", "QRN", "QRO", "QRP", "QRS", "QRT", "QRU",
            "QRV", "QRX", "QRZ", "QSB", "QSL", "QSO", "QSX", "QSY", "QTH", "QUF",
        }
        self.assertEqual({x["code"] for x in Q_DATA["codes"]}, expected)

    def test_lookup_is_case_normalized(self):
        self.assertEqual(trainer.lookup_qcode("qsl")["code"], "QSL")

    def test_qrz_meaning_is_caller_identity(self):
        result = trainer.lookup_qcode("QRZ")
        self.assertIn("calling", result["question_summary"].lower())
        self.assertIsNone(result["legal_verdict"])

    def test_unknown_qcode_rejected(self):
        with self.assertRaises(ValueError):
            trainer.lookup_qcode("QZZ")

    def test_empty_qcode_rejected(self):
        with self.assertRaises(ValueError):
            trainer.lookup_qcode(" ")

    def test_qcode_quiz_is_deterministic(self):
        self.assertEqual(
            trainer.generate_qcode_prompt(seed=17200),
            trainer.generate_qcode_prompt(seed=17200),
        )

    def test_qcode_quiz_invalid_seed_rejected(self):
        with self.assertRaises(ValueError):
            trainer.generate_qcode_prompt(seed=True)


class RSTTrainerTests(unittest.TestCase):
    def test_phone_59(self):
        result = trainer.parse_rst("59", "phone")
        self.assertEqual(result["readability"]["value"], 5)
        self.assertEqual(result["strength"]["value"], 9)
        self.assertIsNone(result["tone"])
        self.assertIsNone(result["legal_verdict"])

    def test_cw_599(self):
        result = trainer.parse_rst("599", "cw")
        self.assertEqual(result["readability"]["value"], 5)
        self.assertEqual(result["strength"]["value"], 9)
        self.assertEqual(result["tone"]["value"], 9)

    def test_phone_cannot_take_three_digits(self):
        with self.assertRaises(ValueError):
            trainer.parse_rst("599", "phone")

    def test_cw_requires_three_digits(self):
        with self.assertRaises(ValueError):
            trainer.parse_rst("59", "cw")

    def test_out_of_range_readability_rejected(self):
        with self.assertRaises(ValueError):
            trainer.parse_rst("09", "phone")

    def test_out_of_range_strength_rejected(self):
        with self.assertRaises(ValueError):
            trainer.parse_rst("50", "phone")

    def test_out_of_range_tone_rejected(self):
        with self.assertRaises(ValueError):
            trainer.parse_rst("590", "cw")

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            trainer.parse_rst("59", "digital")

    def test_rst_prompt_is_deterministic(self):
        self.assertEqual(
            trainer.generate_rst_prompt(mode="cw", seed=17200),
            trainer.generate_rst_prompt(mode="cw", seed=17200),
        )

    def test_rst_prompt_sources_are_grounded(self):
        result = trainer.generate_rst_prompt(mode="phone", seed=1)
        self.assertEqual(
            set(result["source_ids"]),
            {"IARU.R1.EOP.4.2.0", "IARU.R1.VHF.HANDBOOK.10.02"},
        )

    def test_invalid_rst_seed_rejected(self):
        with self.assertRaises(ValueError):
            trainer.generate_rst_prompt(seed=True)


if __name__ == "__main__":
    unittest.main()
