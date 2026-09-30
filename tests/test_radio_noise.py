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


noise = load("radio_noise")
ask = load("ask")
PAYLOAD = json.loads((ROOT / "data" / "radio_noise.json").read_text("utf-8"))
SOURCES = {s["id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))["sources"]}


class RadioNoiseDataTests(unittest.TestCase):
    def assert_rejected(self, mutate, sources=None):
        payload = copy.deepcopy(PAYLOAD)
        mutate(payload)
        with self.assertRaises(noise.RadioNoiseError):
            noise.validate(payload, sources or SOURCES)

    def test_repository_data_is_valid(self):
        noise.validate(PAYLOAD, SOURCES)

    def test_cannot_be_registered_official(self):
        sources = copy.deepcopy(SOURCES)
        sources[PAYLOAD["source_id"]]["source_type"] = "official_technical"
        self.assert_rejected(lambda p: None, sources)

    def test_literal_must_match_value(self):
        self.assert_rejected(lambda p: p["man_made"][0]["c"].update(value=80.0))

    def test_category_order_enforced(self):
        self.assert_rejected(lambda p: p["man_made"][3]["c"].update(value=90.0, literal="90.0"))

    def test_excluded_categories_stay_out(self):
        self.assert_rejected(lambda p: p["man_made"].append(dict(copy.deepcopy(p["man_made"][0]), id="NOISY")))

    def test_provenance_required(self):
        self.assert_rejected(lambda p: p["provenance"].update(commit="PENDING"))
        self.assert_rejected(lambda p: p["man_made"][0]["c"].update(locator="Other.c#L1"))


class RadioNoiseEvaluateTests(unittest.TestCase):
    def test_city_at_10_mhz_is_c_minus_d(self):
        result = noise.evaluate(10.0, PAYLOAD)
        self.assertAlmostEqual(result["man_made"][0]["fa_db"], 76.8 - 27.7)
        self.assertAlmostEqual(result["galactic_fa_db"], 52.0 - 23.0)

    def test_out_of_range_refused(self):
        for f in (1.5, 30.1, 145.0):
            with self.assertRaises(ValueError):
                noise.evaluate(f, PAYLOAD)


class RadioNoiseAnswerTests(unittest.TestCase):
    kb = ask.Knowledge()

    def test_noise_answer_without_legal_verdict(self):
        result = ask.answer("7,1 MHz'te şehir gürültüsü ne kadar?", self.kb)
        routes = [t for t in result["technical_knowledge"] if t["topic"].startswith("Radyo gürültüsü")]
        self.assertIn("Şehir 53,2 dB", " ".join(routes[0]["summary"]))
        self.assertEqual(routes[0]["source_ids"], [PAYLOAD["source_id"]])
        self.assertFalse(any("sınıfı" in line for line in result["short_answer"]))

    def test_out_of_range_not_extrapolated(self):
        result = ask.answer("145 MHz gürültü", self.kb)
        self.assertTrue(any("hesap yapılmaz" in line for line in result["short_answer"]))


if __name__ == "__main__":
    unittest.main()
