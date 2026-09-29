import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
    return sys.modules[name]


vdm = load("validate_digital_modes")
ask = load("ask")
PAYLOAD = json.loads((ROOT / "data" / "digital_modes.json").read_text("utf-8"))
SOURCES = {s["id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))["sources"]}


class DigitalModeDataTests(unittest.TestCase):
    def assert_rejected(self, mutate, sources=None):
        payload = copy.deepcopy(PAYLOAD)
        mutate(payload)
        with self.assertRaises(vdm.DigitalModesError):
            vdm.validate(payload, sources or SOURCES)

    def test_repository_data_is_valid(self):
        vdm.validate(PAYLOAD, SOURCES)

    def test_derived_values(self):
        ft8, ft4 = PAYLOAD["modes"]
        self.assertEqual(vdm.derived(ft8)["tones"], 8)
        self.assertAlmostEqual(vdm.derived(ft8)["tone_spacing_hz"], 6.25)
        self.assertAlmostEqual(vdm.derived(ft8)["transmission_s"], 12.64)
        self.assertEqual(vdm.derived(ft4)["tones"], 4)
        self.assertAlmostEqual(vdm.derived(ft4)["transmission_s"], 5.04)

    def test_pending_hash_rejected(self):
        self.assert_rejected(lambda p: p["provenance"]["files"][0].update(git_blob_sha1="PENDING"))

    def test_symbol_sum_mismatch_rejected(self):
        self.assert_rejected(lambda p: p["modes"][0].update(total_symbols=80))

    def test_ldpc_codeword_mismatch_rejected(self):
        self.assert_rejected(lambda p: p["modes"][1].update(bits_per_symbol=3))

    def test_crc_polynomial_mismatch_rejected(self):
        self.assert_rejected(lambda p: p["shared"].update(crc_polynomial_full="0x2757"))

    def test_transmission_must_fit_slot(self):
        self.assert_rejected(lambda p: p["modes"][0].update(slot_time_s=10.0))

    def test_trust_tier_cannot_be_upgraded(self):
        self.assert_rejected(lambda p: p.update(trust_tier="technical_manual"))
        sources = copy.deepcopy(SOURCES)
        sources["OSS.KGOBA.FT8_LIB"]["source_type"] = "technical_manual"
        with self.assertRaises(vdm.DigitalModesError):
            vdm.validate(PAYLOAD, sources)

    def test_source_url_must_pin_commit(self):
        sources = copy.deepcopy(SOURCES)
        sources["OSS.KGOBA.FT8_LIB"]["url"] = "https://github.com/kgoba/ft8_lib"
        with self.assertRaises(vdm.DigitalModesError):
            vdm.validate(PAYLOAD, sources)

    def test_locator_must_reference_pinned_file(self):
        self.assert_rejected(lambda p: p["modes"][0]["locators"].update(symbol_period_s="ft8/other.h#L1"))


class DigitalModeAnswerTests(unittest.TestCase):
    def test_ft8_answer(self):
        result = ask.answer("FT8 nedir?", ask.Knowledge())
        text = " ".join(result["short_answer"])
        self.assertIn("FT8: 8-FSK", text)
        self.assertIn("ton aralığı 6,250 Hz", text)
        self.assertIn("topluluk kaynağı", text)
        self.assertNotIn("FT4:", text)
        self.assertEqual(result["legal_basis"], [])
        self.assertEqual([s["type"] for s in result["sources"]], ["community"])

    def test_both_modes(self):
        text = " ".join(ask.answer("FT8 ve FT4 farkı", ask.Knowledge())["short_answer"])
        self.assertIn("FT8:", text)
        self.assertIn("FT4: 4-FSK", text)

    def test_not_stated_items_are_disclosed(self):
        details = ask.answer("FT4", ask.Knowledge())["technical_knowledge"][0]["details"]
        self.assertTrue(any("bant genişliği" in line for line in details))

    def test_word_boundary(self):
        self.assertEqual(ask.answer("FT80 nedir?", ask.Knowledge())["technical_knowledge"], [])


if __name__ == "__main__":
    unittest.main()
