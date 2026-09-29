import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location(
        "validate_translations", ROOT / "scripts" / "validate_translations.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_translations"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


vt = load_module()
MANIFEST = json.loads((ROOT / "docs" / "translations.json").read_text("utf-8"))
SOURCES_PAYLOAD = json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))
RULES_PAYLOAD = json.loads((ROOT / "data" / "rules.json").read_text("utf-8"))
SOURCES = vt.registry_map(SOURCES_PAYLOAD, "sources")
RULES = vt.registry_map(RULES_PAYLOAD, "rules")


class TranslationContractTests(unittest.TestCase):
    def test_repository_manifest_validates(self):
        self.assertEqual(
            vt.validate_repository(MANIFEST, SOURCES_PAYLOAD, RULES_PAYLOAD, ROOT),
            2,
        )

    def test_canonical_blob_drift_requires_retranslation(self):
        payload = copy.deepcopy(MANIFEST)
        payload["translations"][0]["canonical_blob_sha1"] = "0" * 40
        with self.assertRaisesRegex(vt.TranslationError, "RETRANSLATION_REQUIRED"):
            vt.validate_repository(payload, SOURCES_PAYLOAD, RULES_PAYLOAD, ROOT)

    def test_legal_verdicts_cannot_be_enabled(self):
        payload = copy.deepcopy(MANIFEST)
        payload["translations"][0]["legal_verdicts"] = True
        with self.assertRaisesRegex(vt.TranslationError, "legal_verdicts"):
            vt.validate_repository(payload, SOURCES_PAYLOAD, RULES_PAYLOAD, ROOT)

    def test_unknown_source_id_is_rejected(self):
        payload = copy.deepcopy(MANIFEST)
        payload["translations"][0]["source_ids"].append("UNKNOWN.SOURCE")
        with self.assertRaisesRegex(vt.TranslationError, "unknown source_ids"):
            vt.validate_repository(payload, SOURCES_PAYLOAD, RULES_PAYLOAD, ROOT)

    def test_pending_source_cannot_be_promoted_into_english_navigation(self):
        payload = copy.deepcopy(MANIFEST)
        payload["translations"][0]["source_ids"].append("TR.BTK.EHK.5809")
        with self.assertRaisesRegex(vt.TranslationError, "not verified"):
            vt.validate_repository(payload, SOURCES_PAYLOAD, RULES_PAYLOAD, ROOT)

    def test_target_must_repeat_all_canonical_ids_and_disclaimers(self):
        source_id = "TR.BTK.FTM.TECH.2022-IK-SYD-245"
        rule_id = "TR.AMATEUR.TECHNICAL_COMPLIANCE"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canonical = root / "canonical.md"
            translation = root / "translation.md"
            canonical.write_text("# canonical\n", encoding="utf-8")
            translation.write_text(
                "Canonical Turkish document path: canonical.md\n"
                "This English page is navigation/translation only. "
                "It does not create or change legal permission.\n"
                f"{rule_id}\n",
                encoding="utf-8",
            )
            record = {
                "id": "TEST.EN",
                "canonical_path": "canonical.md",
                "translation_path": "translation.md",
                "language": "en",
                "translation_kind": "navigation",
                "canonical_blob_sha1": vt.git_blob_sha1(canonical),
                "source_ids": [source_id],
                "rule_ids": [rule_id],
                "legal_verdicts": False,
                "canonical_controls": True,
            }
            with self.assertRaisesRegex(vt.TranslationError, "missing canonical id"):
                vt.validate_record(record, SOURCES, RULES, root)


if __name__ == "__main__":
    unittest.main()
