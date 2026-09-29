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


vdv = load("validate_digital_voice")
ask = load("ask")
PAYLOAD = json.loads((ROOT / "data" / "digital_voice.json").read_text("utf-8"))
SOURCES = {s["id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))["sources"]}


def param(payload, pid):
    return next(p for p in payload["parameters"] if p["id"] == pid)


class DigitalVoiceDataTests(unittest.TestCase):
    def assert_rejected(self, mutate, sources=None):
        payload = copy.deepcopy(PAYLOAD)
        mutate(payload)
        with self.assertRaises(vdv.DigitalVoiceError):
            vdv.validate(payload, sources or SOURCES)

    def test_repository_data_is_valid(self):
        vdv.validate(PAYLOAD, SOURCES)

    def test_literal_expression_parsed(self):
        self.assertEqual(vdv.literal_value("108U * 2U"), 216)
        self.assertEqual(vdv.literal_value("0x55U, 0x2DU, 0x16U"), [0x55, 0x2D, 0x16])

    def test_literal_must_match_value(self):
        self.assert_rejected(lambda p: param(p, "dmr_frame_bits").update(value=265))
        self.assert_rejected(lambda p: param(p, "ysf_sync").update(value=[0xD4, 0x71]))

    def test_dmr_arithmetic(self):
        self.assert_rejected(lambda p: param(p, "dmr_sync_bits").update(value=40, literal="40U"))
        self.assert_rejected(lambda p: param(p, "dmr_ambe_frames_per_burst").update(value=5, literal="5U"))

    def test_sync_must_fit_mask(self):
        self.assert_rejected(lambda p: param(p, "dmr_sync_bs_voice").update(
            value=[0xF7, 0x55, 0xFD, 0x7D, 0xF7, 0x5F, 0x70],
            literal="0xF7U, 0x55U, 0xFDU, 0x7DU, 0xF7U, 0x5FU, 0x70U"))

    def test_dstar_frame_split(self):
        self.assert_rejected(lambda p: param(p, "dstar_voice_bytes").update(value=10, literal="10U"))

    def test_community_tier_and_provenance(self):
        sources = copy.deepcopy(SOURCES)
        sources[PAYLOAD["source_id"]]["source_type"] = "technical_manual"
        self.assert_rejected(lambda p: None, sources)
        self.assert_rejected(lambda p: p["provenance"].update(commit="PENDING"))
        self.assert_rejected(lambda p: param(p, "ysf_sync").update(locator="Other.h#L1"))

    def test_sync_words(self):
        v = vdv.values(PAYLOAD)
        self.assertEqual(vdv.sync_hex(v["dmr_sync_bs_voice"]), "755FD7DF75F7")
        self.assertEqual(vdv.sync_hex(v["dmr_sync_ms_data"]), "D5D7F77FD757")


class DigitalVoiceAnswerTests(unittest.TestCase):
    kb = ask.Knowledge()

    def route(self, question):
        result = ask.answer(question, self.kb)
        return result, [t for t in result["technical_knowledge"] if t["topic"].startswith("Dijital ses")]

    def test_dmr_answer_labelled_and_not_legal(self):
        result, routes = self.route("DMR çerçevesi nasıl?")
        summary = " ".join(routes[0]["summary"])
        self.assertIn("264 bit", summary)
        self.assertIn("topluluk kaynağı", summary)
        self.assertEqual(routes[0]["source_ids"], [PAYLOAD["source_id"]])
        self.assertEqual(result["legal_basis"], [])

    def test_only_requested_modes(self):
        _, routes = self.route("C4FM çerçevesi")
        summary = " ".join(routes[0]["summary"])
        self.assertIn("System Fusion", summary)
        self.assertNotIn("DMR:", summary)

    def test_no_route_without_keyword(self):
        self.assertEqual(self.route("145 MHz nedir?")[1], [])


if __name__ == "__main__":
    unittest.main()
