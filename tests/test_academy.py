import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_academy", ROOT / "scripts" / "validate_academy.py")
va = importlib.util.module_from_spec(spec)
sys.modules["validate_academy"] = va
assert spec.loader is not None
spec.loader.exec_module(va)

MANIFEST = json.loads((ROOT / "academy" / "academy.json").read_text("utf-8"))
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))
RULES = json.loads((ROOT / "data" / "rules.json").read_text("utf-8"))
CANDIDATES = json.loads((ROOT / "data" / "source_candidates.json").read_text("utf-8"))


def module_by_id(payload, module_id):
    return next(m for m in payload["modules"] if m["id"] == module_id)


class AcademyManifestTests(unittest.TestCase):
    def validate(self, manifest=MANIFEST, candidates=CANDIDATES):
        va.validate_manifest(manifest, SOURCES, RULES, candidates)

    def mutate(self, module_id, **changes):
        payload = copy.deepcopy(MANIFEST)
        module_by_id(payload, module_id).update(changes)
        return payload

    def test_repository_manifest_is_valid(self):
        self.validate()

    def test_duplicate_module_id_rejected(self):
        payload = copy.deepcopy(MANIFEST)
        payload["modules"].append(copy.deepcopy(payload["modules"][0]))
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_source_grounded_rejects_pending_source(self):
        payload = self.mutate(
            "ACADEMY.TR.EXAM-OPERATIONS",
            source_ids=["TR.BTK.EHK.5809"],
        )
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_legal_module_rejects_amateur_source(self):
        payload = self.mutate(
            "ACADEMY.TR.CORE-COMPLIANCE",
            source_ids=["IARU.R1.BANDPLANS"],
            rule_ids=["IARU.R1.NATIONAL_RULES_PREVAIL"],
        )
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_legal_module_requires_legal_rule(self):
        payload = self.mutate("ACADEMY.TR.CORE-COMPLIANCE", rule_ids=[])
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_rule_source_must_be_explicitly_listed(self):
        payload = self.mutate(
            "ACADEMY.IARU.BANDPLAN-PRACTICE",
            source_ids=["IARU.R1.VHF.HANDBOOK.10.02"],
        )
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_nonlegal_module_cannot_hide_legal_rule(self):
        payload = self.mutate(
            "ACADEMY.TR.EXAM-OPERATIONS",
            source_ids=["TR.BTK.FTM.TECH.2022-IK-SYD-245"],
            rule_ids=["TR.AMATEUR.DUMMY_LOAD"],
        )
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_educational_only_rejects_source_or_rule_claim(self):
        with self.assertRaises(SystemExit):
            self.validate(
                self.mutate(
                    "ACADEMY.TOOL.GRID-LOCATOR",
                    source_ids=["IARU.R1.BANDPLANS"],
                )
            )
        with self.assertRaises(SystemExit):
            self.validate(
                self.mutate(
                    "ACADEMY.TOOL.GRID-LOCATOR",
                    rule_ids=["IARU.R1.NATIONAL_RULES_PREVAIL"],
                )
            )

    def test_educational_only_rejects_legal_content(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("ACADEMY.TOOL.GRID-LOCATOR", legal_content=True))

    def test_educational_only_candidate_must_be_community(self):
        payload = self.mutate(
            "ACADEMY.TOOL.GRID-LOCATOR",
            candidate_refs=["CAND.TR.TRAC.EXAM_STUDY"],
        )
        with self.assertRaises(SystemExit):
            self.validate(payload)

    def test_community_candidate_must_disclaim_legal_claims(self):
        candidates = copy.deepcopy(CANDIDATES)
        candidate = next(
            c for c in candidates["candidates"]
            if c["id"] == "CAND.COMMUNITY.ARCH-YUNUS.AMATOR-TELSIZ-REHBERI"
        )
        candidate["cannot_support"] = ["turkish_permission"]
        with self.assertRaises(SystemExit):
            self.validate(candidates=candidates)

    def test_legal_verdicts_are_always_rejected(self):
        with self.assertRaises(SystemExit):
            self.validate(self.mutate("ACADEMY.TR.CORE-COMPLIANCE", legal_verdicts=True))

    def test_academy_readme_lists_every_module(self):
        doc = (ROOT / "academy" / "README.md").read_text("utf-8")
        for module in MANIFEST["modules"]:
            with self.subTest(module=module["id"]):
                self.assertIn(f"`{module['id']}`", doc)


if __name__ == "__main__":
    unittest.main()
