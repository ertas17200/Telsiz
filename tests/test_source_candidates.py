import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_knowledge", ROOT / "scripts" / "validate_knowledge.py")
vk = importlib.util.module_from_spec(spec)
sys.modules["validate_knowledge"] = vk
assert spec.loader is not None
spec.loader.exec_module(vk)

SOURCES = {s["id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))["sources"]}
RULES = json.loads((ROOT / "data" / "rules.json").read_text("utf-8"))["rules"]
TABLE = json.loads((ROOT / "data" / "frequency_table.json").read_text("utf-8"))
CANDIDATES = json.loads((ROOT / "data" / "source_candidates.json").read_text("utf-8"))
CONFLICTS = set(vk.CONFLICT_HEADING_RE.findall((ROOT / "docs" / "SOURCE_CONFLICTS.md").read_text("utf-8")))


def by_id(payload, cand_id):
    return next(c for c in payload["candidates"] if c["id"] == cand_id)


class SourceCandidateTests(unittest.TestCase):
    def validate(self, payload=CANDIDATES, rules=RULES, table=TABLE):
        vk.validate_source_candidates(payload, SOURCES, rules, table, CONFLICTS)

    def mutate(self, cand_id, **changes):
        payload = copy.deepcopy(CANDIDATES)
        by_id(payload, cand_id).update(changes)
        return payload

    def test_repository_candidates_are_valid(self):
        self.validate()

    def test_conflict_headings_are_parsed(self):
        self.assertEqual(CONFLICTS, {"TR-BTK-NUMBERING-001", "TR-BTK-EMISSION-001", "TR-BTK-UNIT-001"})

    def test_no_candidate_claims_a_canonical_url(self):
        self.assertTrue(all(c["canonical_url"] is None for c in CANDIDATES["candidates"]))
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("CAND.ITU.RR", canonical_url="https://www.itu.int/x"))

    def test_rule_cannot_cite_candidate(self):
        rules = copy.deepcopy(RULES)
        rules[0]["source_id"] = "CAND.ITU.RR"
        with self.assertRaises(SystemExit):
            self.validate(rules=rules)

    def test_frequency_row_cannot_cite_candidate(self):
        table = copy.deepcopy(TABLE)
        table["rows"][0]["source_id"] = "CAND.TR.BTK.NATIONAL_FREQUENCY_PLAN"
        with self.assertRaises(SystemExit):
            self.validate(table=table)

    def test_candidate_id_cannot_shadow_registered_source(self):
        sources = copy.deepcopy(SOURCES)
        sources["CAND.ITU.RR"] = copy.deepcopy(SOURCES["TR.BTK.EHK.5809"])
        with self.assertRaises(SystemExit):
            vk.validate_source_candidates(CANDIDATES, sources, RULES, TABLE, CONFLICTS)

    def test_candidate_id_requires_prefix(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("CAND.ITU.RR", id="ITU.RR"))

    def test_duplicate_candidate_rejected(self):
        payload = copy.deepcopy(CANDIDATES)
        payload["candidates"].append(copy.deepcopy(payload["candidates"][0]))
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_non_official_candidate_must_disclaim_legal_claims(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("CAND.COMMUNITY.ARCH-YUNUS.AMATOR-TELSIZ", cannot_support=[]))
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("CAND.TR.TRAC.REPEATER_LIST", cannot_support=["turkish_permission"]))

    def test_every_non_official_candidate_disclaims_legal_claims(self):
        for cand in CANDIDATES["candidates"]:
            if not cand["expected_source_type"].startswith("official_"):
                with self.subTest(cand=cand["id"]):
                    self.assertIn("legal_claims", cand["cannot_support"])

    def test_unknown_conflict_reference_rejected(self):
        payload = copy.deepcopy(CANDIDATES)
        by_id(payload, "CAND.TR.BTK.FTM.TECH.AMENDMENT_HISTORY")["unlocks"]["conflicts"].append("TR-BTK-FAKE-999")
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_unknown_rule_reference_rejected(self):
        payload = copy.deepcopy(CANDIDATES)
        by_id(payload, "CAND.ITU.RR")["unlocks"]["rules"] = ["TR.AMATEUR.DOES_NOT_EXIST"]
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_unknown_field_reference_rejected(self):
        payload = copy.deepcopy(CANDIDATES)
        by_id(payload, "CAND.TR.BTK.NATIONAL_FREQUENCY_PLAN")["unlocks"]["fields"] = ["allocation"]
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_unregistered_related_source_rejected(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("CAND.ITU.RR", related_sources=["ITU.RR.2024"]))

    def test_invalid_phase_rejected(self):
        payload = copy.deepcopy(CANDIDATES)
        by_id(payload, "CAND.ITU.RR")["unlocks"]["phases"] = ["P12"]
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_access_domains_must_be_hostnames(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("CAND.ITU.RR", required_access_domains=["https://www.itu.int/"]))

    def test_invalid_status_rejected(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("CAND.ITU.RR", status="verified"))

    def test_entry_point_must_be_https(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("CAND.ITU.RR", search_entry_point="http://www.itu.int/"))

    def test_candidate_doc_lists_every_candidate(self):
        doc = (ROOT / "docs" / "SOURCE_CANDIDATES.md").read_text("utf-8")
        for cand in CANDIDATES["candidates"]:
            with self.subTest(cand=cand["id"]):
                self.assertIn(f"`{cand['id']}`", doc)


if __name__ == "__main__":
    unittest.main()
