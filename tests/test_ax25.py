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


vax = load("validate_ax25")
ask = load("ask")
PAYLOAD = json.loads((ROOT / "data" / "ax25_parameters.json").read_text("utf-8"))
SOURCES = {s["id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))["sources"]}


def param(payload, pid):
    return next(p for p in payload["parameters"] if p["id"] == pid)


class Ax25DataTests(unittest.TestCase):
    def assert_rejected(self, mutate, sources=None):
        payload = copy.deepcopy(PAYLOAD)
        mutate(payload)
        with self.assertRaises(vax.Ax25Error):
            vax.validate(payload, sources or SOURCES)

    def test_repository_data_is_valid(self):
        vax.validate(PAYLOAD, SOURCES)

    def test_literal_must_match_value(self):
        self.assert_rejected(lambda p: param(p, "aprs_pid").update(value=0xCF))

    def test_address_arithmetic(self):
        self.assert_rejected(lambda p: param(p, "max_repeaters").update(value=7, literal="7"))

    def test_polynomial_must_be_reflected_ccitt(self):
        self.assert_rejected(lambda p: param(p, "fcs_polynomial_reflected").update(value=0x1021, literal="0x1021"))

    def test_community_tier_locked(self):
        sources = copy.deepcopy(SOURCES)
        sources[PAYLOAD["source_id"]]["source_type"] = "technical_manual"
        self.assert_rejected(lambda p: None, sources)
        self.assert_rejected(lambda p: p.update(trust_tier="official"))

    def test_provenance_required(self):
        self.assert_rejected(lambda p: p["provenance"].update(commit="PENDING"))
        self.assert_rejected(lambda p: param(p, "hdlc_flag").update(locator="src/other.c#L1"))
        self.assert_rejected(lambda p: p["parameters"].pop(0))

    def test_fcs_matches_crc16_x25_check_value(self):
        # 0x906E is the published check value of CRC-16/X-25 over "123456789".
        self.assertEqual(vax.fcs(b"123456789", vax.values(PAYLOAD)), 0x906E)

    def test_generated_table_entry_128_is_polynomial(self):
        self.assertEqual(vax.fcs_table(0x8408)[128], 0x8408)


class Ax25AnswerTests(unittest.TestCase):
    kb = ask.Knowledge()

    def test_answer_is_labelled_community_and_not_legal(self):
        result = ask.answer("AX.25 FCS nasıl hesaplanır?", self.kb)
        routes = [t for t in result["technical_knowledge"] if t["topic"].startswith("AX.25")]
        self.assertEqual(len(routes), 1)
        summary = " ".join(routes[0]["summary"])
        self.assertIn("0x8408", summary)
        self.assertIn("topluluk kaynağı", summary)
        self.assertEqual(routes[0]["source_ids"], [PAYLOAD["source_id"]])
        self.assertEqual(result["legal_basis"], [])

    def test_no_route_without_keyword(self):
        result = ask.answer("145 MHz nedir?", self.kb)
        self.assertFalse(any(t["topic"].startswith("AX.25") for t in result["technical_knowledge"]))


if __name__ == "__main__":
    unittest.main()
