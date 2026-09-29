import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location(
        "validate_legal_corroborations",
        ROOT / "scripts" / "validate_legal_corroborations.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_legal_corroborations"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


vc = load_module()
CORR = json.loads((ROOT / "data" / "legal_corroborations.json").read_text("utf-8"))
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))
RULES = json.loads((ROOT / "data" / "rules.json").read_text("utf-8"))
FREQ = json.loads((ROOT / "data" / "frequency_table.json").read_text("utf-8"))


class LegalCorroborationTests(unittest.TestCase):
    def validate(self, payload):
        return vc.validate_repository(payload, SOURCES, RULES, FREQ)

    def test_repository_registry_is_valid(self):
        self.assertEqual(self.validate(CORR), 3)

    def test_corroboration_cannot_promote_canonical_source(self):
        payload = copy.deepcopy(CORR)
        payload["records"][0]["promotes_canonical_source"] = True
        with self.assertRaisesRegex(vc.CorroborationError, "cannot promote"):
            self.validate(payload)

    def test_corroboration_cannot_ground_verified_rule(self):
        payload = copy.deepcopy(CORR)
        payload["records"][0]["may_ground_verified_legal_rule"] = True
        with self.assertRaisesRegex(vc.CorroborationError, "cannot ground"):
            self.validate(payload)

    def test_corroboration_cannot_emit_legal_verdict(self):
        payload = copy.deepcopy(CORR)
        payload["records"][0]["legal_verdicts"] = True
        with self.assertRaisesRegex(vc.CorroborationError, "legal_verdicts"):
            self.validate(payload)

    def test_non_btk_host_is_rejected(self):
        payload = copy.deepcopy(CORR)
        payload["records"][0]["corroborating_url"] = "https://example.com/not-official"
        with self.assertRaisesRegex(vc.CorroborationError, "official btk.gov.tr"):
            self.validate(payload)

    def test_unknown_canonical_source_is_rejected(self):
        payload = copy.deepcopy(CORR)
        payload["records"][0]["canonical_source_id"] = "TR.UNKNOWN.LEGAL"
        with self.assertRaisesRegex(vc.CorroborationError, "unknown canonical_source_id"):
            self.validate(payload)

    def test_exact_quote_observation_requires_locator(self):
        payload = copy.deepcopy(CORR)
        payload["records"][0]["references"][0]["locator"] = ""
        with self.assertRaisesRegex(vc.CorroborationError, "locator"):
            self.validate(payload)

    def test_current_5809_source_remains_pending(self):
        source = next(s for s in SOURCES["sources"] if s["id"] == "TR.BTK.EHK.5809")
        self.assertEqual(source["verification_status"], "pending")
        self.assertIsNone(source["verified_at"])

    def test_current_ftm_regulation_source_remains_pending(self):
        source = next(
            s for s in SOURCES["sources"]
            if s["id"] == "TR.BTK.FTM.REGULATION.2018"
        )
        self.assertEqual(source["verification_status"], "pending")
        self.assertIsNone(source["verified_at"])

    def test_no_rule_or_frequency_row_cites_corroboration_id(self):
        ids = {r["id"] for r in CORR["records"]}
        self.assertTrue(ids.isdisjoint({r["source_id"] for r in RULES["rules"]}))
        self.assertTrue(ids.isdisjoint({r["source_id"] for r in FREQ["rows"]}))


if __name__ == "__main__":
    unittest.main()
