import importlib.util
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


emc = load_module("emergency_comms")
registry = emc.load_registry()


class EmergencyCommunicationsDataTests(unittest.TestCase):
    def test_validator_passes(self):
        out = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_emergency_comms.py")],
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertIn("5 official-context item(s)", out)
        self.assertIn("4 amateur-practice item(s)", out)

    def test_authority_contract_is_fail_closed(self):
        c = registry["authority_contract"]
        self.assertEqual(c["legal_permission_from_this_layer"], "PROHIBITED")
        self.assertEqual(c["frequency_inference"], "PROHIBITED")
        self.assertFalse(c["amateur_status_implies_official_assignment"])
        self.assertFalse(c["emergency_context_expands_transmit_permission"])

    def test_tamp_levels_are_grounded(self):
        result = emc.answer_topic("TAMP S3 ne demek?", registry)
        text = " ".join(result["short"])
        self.assertIn("S3", text)
        self.assertIn("ulusal destek", text)
        self.assertEqual(result["source_ids"], ["TR.AFAD.TAMP.2022"])

    def test_emergency_frequency_is_not_invented(self):
        result = emc.answer_topic("Afet frekansı hangisi?", registry)
        text = " ".join(result["short"])
        self.assertIn("tek/genel bir afet frekansı", text)
        self.assertEqual(result["legal_permission_from_this_layer"], "PROHIBITED")
        self.assertEqual(result["frequency_inference"], "PROHIBITED")

    def test_amateur_status_does_not_imply_assignment(self):
        result = emc.answer_topic("Amatör telsizci afet anında resmî görevli midir?", registry)
        text = " ".join(result["short"])
        self.assertIn("tek başına", text)
        self.assertIn("resmî görevlendirme", text)


class EmergencyAskRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ask = load_module("ask")
        cls.kb = cls.ask.Knowledge()

    def test_tamp_route(self):
        result = self.ask.answer("TAMP nedir ve afet haberleşmesinde ne ifade eder?", self.kb)
        text = " ".join(result["short_answer"])
        self.assertIn("TAMP", text)
        self.assertIn("IARU", text)
        self.assertIn("TR.AFAD.TAMP.2022", {s["source_id"] for s in result["sources"]})
        self.assertIn("IARU.R1.EMCOMM.PROCEDURES", {s["source_id"] for s in result["sources"]})

    def test_emergency_frequency_route_stays_fail_closed(self):
        result = self.ask.answer("Afet durumunda 145.500 MHz otomatik olarak serbest mi?", self.kb)
        text = " ".join(result["short_answer"]).lower()
        self.assertIn("yayın izni", text)
        self.assertIn("bilinmiyor", text)
        self.assertNotIn("otomatik olarak serbesttir", text)

    def test_s4_route(self):
        result = self.ask.answer("TAMP S4 ne demek?", self.kb)
        self.assertIn("uluslararası destek", " ".join(result["short_answer"]))

    def test_off_topic_does_not_route_emergency(self):
        result = self.ask.answer("QTH ne demek?", self.kb)
        topics = {x["topic"] for x in result["technical_knowledge"]}
        self.assertNotIn("Acil durum / afet haberleşmesi", topics)


if __name__ == "__main__":
    unittest.main()
