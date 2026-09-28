import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("morse_trainer", ROOT / "scripts" / "morse_trainer.py")
morse = importlib.util.module_from_spec(spec)
sys.modules["morse_trainer"] = morse
assert spec.loader is not None
spec.loader.exec_module(morse)

DATA = json.loads((ROOT / "data" / "morse_code.json").read_text("utf-8"))


class MorseTrainerTests(unittest.TestCase):
    def test_data_covers_exact_basic_subset(self):
        self.assertEqual(set(DATA["characters"]), set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))

    def test_sos_encoding(self):
        self.assertEqual(morse.encode_text("SOS"), "... --- ...")

    def test_digits_encoding(self):
        self.assertEqual(morse.encode_text("73"), "--... ...--")

    def test_word_separator(self):
        self.assertEqual(morse.encode_text("CQ TEST"), "-.-. --.- / - . ... -")

    def test_decode_roundtrip(self):
        text = "HELLO 73"
        self.assertEqual(morse.decode_morse(morse.encode_text(text)), text)

    def test_lowercase_input_is_normalized(self):
        self.assertEqual(morse.encode_text("sos"), "... --- ...")

    def test_unsupported_text_character_rejected(self):
        with self.assertRaises(ValueError):
            morse.encode_text("HELLO!")

    def test_unsupported_signal_rejected(self):
        with self.assertRaises(ValueError):
            morse.decode_morse("......")

    def test_empty_text_rejected(self):
        with self.assertRaises(ValueError):
            morse.encode_text("   ")

    def test_empty_morse_word_rejected(self):
        with self.assertRaises(ValueError):
            morse.decode_morse("... / / ---")

    def test_quiz_is_seed_deterministic(self):
        first = morse.generate_prompt(length=12, seed=17200)
        second = morse.generate_prompt(length=12, seed=17200)
        self.assertEqual(first, second)

    def test_quiz_different_seed_changes_prompt(self):
        first = morse.generate_prompt(length=20, seed=1)
        second = morse.generate_prompt(length=20, seed=2)
        self.assertNotEqual(first["text"], second["text"])

    def test_quiz_has_source_and_no_legal_verdict(self):
        result = morse.generate_prompt(length=5, seed=1)
        self.assertEqual(result["source_id"], "ITU.R.M1677.1")
        self.assertIsNone(result["legal_verdict"])

    def test_invalid_quiz_length_rejected(self):
        for value in (0, 101, True, 1.5):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    morse.generate_prompt(length=value)

    def test_invalid_seed_rejected(self):
        with self.assertRaises(ValueError):
            morse.generate_prompt(seed=True)

    def test_unsupported_quiz_alphabet_rejected(self):
        with self.assertRaises(ValueError):
            morse.generate_prompt(alphabet="ABC!")


if __name__ == "__main__":
    unittest.main()
