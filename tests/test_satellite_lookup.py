import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


sat = load_module("satellite_lookup")
registry = sat.load_registry()


class SatelliteDataTests(unittest.TestCase):
    def test_validator_passes(self):
        out = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_satellites.py")],
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertIn("4 satellite(s), 5 selected", out)

    def test_license_and_authority_are_fail_closed(self):
        self.assertEqual(registry["license"]["spdx_like"], "CC-BY-SA-4.0")
        self.assertEqual(registry["authority"], "community_open_data")
        self.assertEqual(registry["decision_authority"], "technical_reference_only")
        self.assertEqual(registry["legal_status"], "UNKNOWN")
        self.assertEqual(registry["permission_inference"], "PROHIBITED")

    def test_iss_aprs(self):
        result = sat.lookup("ISS", registry)
        tx = result["matches"][0]["transmitters"][0]
        self.assertEqual((tx["downlink"]["low_hz"], tx["uplink"]["low_hz"], tx["baud"]),
                         (145825000, 145825000, 1200))

    def test_so50_exact_alias(self):
        result = sat.lookup("SO-50", registry)
        tx = result["matches"][0]["transmitters"][0]
        self.assertEqual(tx["uplink"]["low_hz"], 145850000)
        self.assertEqual(tx["downlink"]["low_hz"], 436795000)
        self.assertEqual(tx["access_tone_hz"], 67.0)

    def test_ao73_linear_transponder(self):
        tx = sat.lookup("AO-73", registry)["matches"][0]["transmitters"][0]
        self.assertEqual((tx["uplink"]["low_hz"], tx["uplink"]["high_hz"]), (435130000, 435150000))
        self.assertEqual((tx["downlink"]["low_hz"], tx["downlink"]["high_hz"]), (145950000, 145970000))
        self.assertTrue(tx["inverted"])

    def test_ao91_has_no_ctcss_in_snapshot(self):
        tx = sat.lookup("AO-91", registry)["matches"][0]["transmitters"][0]
        self.assertEqual(tx["uplink"]["low_hz"], 435250000)
        self.assertEqual(tx["downlink"]["low_hz"], 145960000)
        self.assertIsNone(tx["access_tone_hz"])
        self.assertIn("no CTCSS", tx["description"])

    def test_unknown_is_not_fuzzy_guessed(self):
        result = sat.lookup("AO-9", registry)
        self.assertEqual(result["status"], "not_found")
        self.assertEqual(result["legal_status"], "UNKNOWN")
        self.assertEqual(result["permission_inference"], "PROHIBITED")

    def test_mentions_require_exact_alias_boundaries(self):
        hits = sat.find_mentions("AO-91 uydusunun uplink frekansı nedir?", registry)
        self.assertEqual([x["norad_id"] for x in hits], [43017])
        self.assertEqual(sat.find_mentions("AO-9 uydusu nedir?", registry), [])


class SatelliteAskRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ask = load_module("ask")
        cls.kb = cls.ask.Knowledge()

    def test_so50_route(self):
        result = self.ask.answer("SO-50 uydu frekansları nedir?", self.kb)
        text = " ".join(result["short_answer"])
        self.assertIn("SO-50", text)
        self.assertIn("145.85 MHz", text)
        self.assertIn("436.795 MHz", text)
        self.assertIn("SATNOGS.DB.SATELLITE_TRANSMITTERS", {s["source_id"] for s in result["sources"]})
        self.assertNotIn("izin var", text.lower())

    def test_iss_aprs_route(self):
        result = self.ask.answer("ISS APRS hangi frekansta?", self.kb)
        self.assertIn("145.825 MHz", " ".join(result["short_answer"]))
        self.assertIn("Uydu verisi teknik referanstır", " ".join(result["short_answer"]))

    def test_ao73_route(self):
        result = self.ask.answer("AO-73 transponder uplink downlink nedir?", self.kb)
        text = " ".join(result["short_answer"])
        self.assertIn("435.13–435.15 MHz LSB", text)
        self.assertIn("145.95–145.97 MHz USB", text)

    def test_unknown_satellite_is_not_invented(self):
        result = self.ask.answer("AO-999 uydu frekansı nedir?", self.kb)
        self.assertTrue(result["fail_closed"])
        self.assertNotIn("SATNOGS.DB.SATELLITE_TRANSMITTERS", {s["source_id"] for s in result["sources"]})


if __name__ == "__main__":
    unittest.main()
