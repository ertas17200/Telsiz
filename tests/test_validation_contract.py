import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_knowledge.py"
SPEC = importlib.util.spec_from_file_location("validate_knowledge", MODULE_PATH)
vk = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(vk)


def source(source_id="TR.TEST", source_type="official_legal", verification="verified", legal_status="current"):
    return {
        "id": source_id,
        "source_type": source_type,
        "verification_status": verification,
        "legal_status": legal_status,
    }


def rule(source_id="TR.TEST", authority="legal", verification="verified"):
    return {
        "id": "TR.TEST.RULE",
        "jurisdiction": "TR",
        "topic": "test",
        "rule_type": "condition",
        "authority": authority,
        "claim": "Test için yeterince uzun doğrulanmış bir iddia.",
        "source_id": source_id,
        "source_locator": {"article": "MADDE 1"},
        "verification_status": verification,
        "verified_at": "2026-09-28T18:37:00Z" if verification == "verified" else None,
        "conditions": [],
        "answer_tags": ["test"],
    }


class RuleGroundingContractTests(unittest.TestCase):
    def test_verified_legal_rule_accepts_current_verified_legal_source(self):
        item = rule()
        vk.validate_rule(item, 0, set(), {"TR.TEST": source()})

    def test_verified_rule_rejects_pending_source(self):
        item = rule()
        with self.assertRaises(SystemExit):
            vk.validate_rule(
                item,
                0,
                set(),
                {"TR.TEST": source(verification="pending")},
            )

    def test_legal_rule_rejects_amateur_publication(self):
        item = rule(source_id="IARU.TEST")
        with self.assertRaises(SystemExit):
            vk.validate_rule(
                item,
                0,
                set(),
                {
                    "IARU.TEST": source(
                        source_id="IARU.TEST",
                        source_type="amateur_association",
                        legal_status="not_applicable",
                    )
                },
            )

    def test_verified_legal_rule_rejects_noncurrent_source(self):
        item = rule()
        with self.assertRaises(SystemExit):
            vk.validate_rule(
                item,
                0,
                set(),
                {"TR.TEST": source(legal_status="superseded")},
            )


if __name__ == "__main__":
    unittest.main()
