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


aprs = load("aprs_deviceid")
ask = load("ask")
PAYLOAD = json.loads((ROOT / "data" / "aprs_deviceid.json").read_text("utf-8"))
SOURCES = {s["id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))["sources"]}


def fake(*patterns):
    return {"tocalls": [{"tocall": p, "model": p, "locator": "tocalls.yaml#L1"} for p in patterns]}


class AprsDataTests(unittest.TestCase):
    def assert_rejected(self, mutate, sources=None):
        payload = copy.deepcopy(PAYLOAD)
        mutate(payload)
        with self.assertRaises(aprs.AprsDeviceIdError):
            aprs.validate(payload, sources or SOURCES)

    def test_repository_data_is_valid(self):
        aprs.validate(PAYLOAD, SOURCES)

    def test_no_contact_fields_copied(self):
        self.assertFalse(any("contact" in e for e in PAYLOAD["tocalls"]))
        self.assert_rejected(lambda p: p["tocalls"][0].update(contact="x@example.org"))

    def test_license_notice_required(self):
        self.assert_rejected(lambda p: p["license"].update(id="MIT"))
        self.assert_rejected(lambda p: p["license"].update(attribution=""))
        self.assert_rejected(lambda p: p["license"].update(adaptation=""))

    def test_provenance_required(self):
        self.assert_rejected(lambda p: p["provenance"].update(commit="PENDING"))
        self.assert_rejected(lambda p: p["provenance"]["files"][0].update(sha256="PENDING"))
        self.assert_rejected(lambda p: p["tocalls"][0].update(locator="other.yaml#L1"))

    def test_source_must_not_be_legal(self):
        sources = copy.deepcopy(SOURCES)
        sources[PAYLOAD["source_id"]]["source_type"] = "official_legal"
        self.assert_rejected(lambda p: None, sources)

    def test_unverified_source_rejected(self):
        sources = copy.deepcopy(SOURCES)
        sources[PAYLOAD["source_id"]]["verification_status"] = "pending"
        self.assert_rejected(lambda p: None, sources)

    def test_duplicate_and_unknown_class_rejected(self):
        self.assert_rejected(lambda p: p["tocalls"].append(copy.deepcopy(p["tocalls"][0])))
        self.assert_rejected(lambda p: p["tocalls"][0].update({"class": "nonexistent"}))


class AprsLookupTests(unittest.TestCase):
    def test_exact_before_wildcard(self):
        result = aprs.lookup("APAGW", PAYLOAD)
        self.assertEqual((result["status"], result["matches"][0]["tocall"]), ("exact", "APAGW"))

    def test_longest_wildcard_wins(self):
        result = aprs.lookup("APXYZ1", fake("APXY??", "APXYZ?"))
        self.assertEqual((result["status"], result["matches"][0]["tocall"]), ("wildcard", "APXYZ?"))

    def test_digit_and_star_wildcards(self):
        self.assertEqual(aprs.lookup("APD123", fake("APDnnn"))["status"], "wildcard")
        self.assertEqual(aprs.lookup("APDABC", fake("APDnnn"))["status"], "not_found")
        self.assertEqual(aprs.lookup("APZ9", fake("APZ*"))["status"], "wildcard")

    def test_equal_matches_are_ambiguous(self):
        result = aprs.lookup("APD12D", fake("APDnn?", "APD?n?"))
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(len(result["matches"]), 2)

    def test_ssid_stripped_and_real_entries(self):
        result = aprs.lookup("apdw16-3", PAYLOAD)
        self.assertEqual(result["tocall"], "APDW16")
        self.assertEqual(result["matches"][0]["model"], "DireWolf")

    def test_invalid_tocall_rejected(self):
        with self.assertRaises(ValueError):
            aprs.normalize_tocall("AP DW")


class MiceLookupTests(unittest.TestCase):
    def test_new_style_suffix(self):
        result = aprs.lookup_mice("_3", PAYLOAD)
        self.assertEqual(result["status"], "found")
        self.assertEqual([(m["kind"], m["model"]) for m in result["matches"]], [("mice", "FT5D")])

    def test_legacy_prefix_and_pair(self):
        self.assertEqual([m["model"] for m in aprs.lookup_mice(">", PAYLOAD)["matches"]], ["TH-D7A"])
        self.assertEqual([m["model"] for m in aprs.lookup_mice(">=", PAYLOAD)["matches"]], ["TH-D72"])

    def test_unknown_code_not_guessed(self):
        self.assertEqual(aprs.lookup_mice("zz", PAYLOAD)["status"], "not_found")
        with self.assertRaises(ValueError):
            aprs.lookup_mice("abc", PAYLOAD)

    def test_mice_validation(self):
        def rejected(mutate):
            payload = copy.deepcopy(PAYLOAD)
            mutate(payload)
            with self.assertRaises(aprs.AprsDeviceIdError):
                aprs.validate(payload, SOURCES)
        rejected(lambda p: p["mice"][0].update(suffix="_"))
        rejected(lambda p: p["mice"][0].update(contact="x@example.org"))
        rejected(lambda p: p["micelegacy"][0].pop("prefix"))
        rejected(lambda p: p["mice"].append(copy.deepcopy(p["mice"][0])))
        rejected(lambda p: p.update(mice=[]))


class AprsAnswerTests(unittest.TestCase):
    kb = ask.Knowledge()

    def route(self, question):
        result = ask.answer(question, self.kb)
        return result, [t for t in result["technical_knowledge"] if t["topic"].startswith("APRS")]

    def test_device_answer_is_sourced_and_not_legal(self):
        result, routes = self.route("APRS APDW16 hangi cihaz?")
        self.assertEqual(len(routes), 1)
        self.assertIn("DireWolf", " ".join(routes[0]["summary"]))
        self.assertEqual(routes[0]["source_ids"], [PAYLOAD["source_id"]])
        self.assertEqual(result["legal_basis"], [])
        self.assertIn("CC BY-SA 2.0", " ".join(routes[0]["details"]))

    def test_unknown_tocall_is_not_guessed(self):
        _, routes = self.route("APRS APY03 nedir?")
        self.assertIn("eşleşen kayıt yok", " ".join(routes[0]["summary"]))

    def test_mice_answer(self):
        _, routes = self.route('Mic-E "_3" hangi cihaz?')
        self.assertIn("FT5D", " ".join(routes[0]["summary"]))

    def test_no_route_without_aprs_keyword(self):
        _, routes = self.route("APDW16 nedir?")
        self.assertEqual(routes, [])


if __name__ == "__main__":
    unittest.main()
