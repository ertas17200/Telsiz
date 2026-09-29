import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location("artifact_gate", ROOT / "scripts" / "artifact_gate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["artifact_gate"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gate = load_module()
SOURCES_PAYLOAD = json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))
SOURCES = gate.source_map(SOURCES_PAYLOAD)
ARTIFACTS = json.loads((ROOT / "data" / "artifacts.json").read_text("utf-8"))
SOURCE_ID = "TR.BTK.FTM.TECH.2022-IK-SYD-245"


class ArtifactRegistryTests(unittest.TestCase):
    def test_repository_registry_is_fail_closed_and_valid(self):
        self.assertEqual(gate.validate_registry(ARTIFACTS, SOURCES_PAYLOAD), 4)
        record = next(x for x in ARTIFACTS["artifacts"] if x["source_id"] == SOURCE_ID)
        self.assertEqual(record["artifact_status"], "verified_bytes")
        self.assertEqual(
            record["sha256"],
            "sha256:eff832fc30df1adf60e4a8c514a6069154d526d3ab88ae803b51a5536d103db0",
        )
        self.assertEqual(record["size_bytes"], 508766)
        self.assertEqual(record["change_status"], "UNCHANGED")
        self.assertFalse(record["reverify_required"])
        self.assertEqual(record["sha256"], SOURCES[SOURCE_ID]["content_sha256"])

    def test_p1_p2_p3_remain_fail_closed_awaiting_bytes(self):
        pending_ids = {
            "TR.BTK.EHK.5809",
            "TR.BTK.FTM.REGULATION.2018",
            "TR.KEGM.AMATEUR.EXAM.REGULATION",
        }
        records = {x["source_id"]: x for x in ARTIFACTS["artifacts"]}
        self.assertTrue(pending_ids.issubset(records))
        for source_id in pending_ids:
            with self.subTest(source_id=source_id):
                record = records[source_id]
                self.assertEqual(record["artifact_status"], "awaiting_bytes")
                self.assertIsNone(record["fetched_at"])
                self.assertIsNone(record["size_bytes"])
                self.assertIsNone(record["sha256"])
                self.assertEqual(record["change_status"], "UNKNOWN")
                self.assertTrue(record["reverify_required"])
                self.assertEqual(record["canonical_url"], SOURCES[source_id]["url"])
                self.assertEqual(record["expected_mime_type"], "text/html")

    def test_pending_record_rejects_fake_hash(self):
        payload = copy.deepcopy(ARTIFACTS)
        record = next(x for x in payload["artifacts"] if x["source_id"] == "TR.BTK.EHK.5809")
        record["sha256"] = "sha256:" + "a" * 64
        with self.assertRaises(gate.GateError):
            gate.validate_registry(payload, SOURCES_PAYLOAD)

    def test_pending_record_rejects_false_reverify(self):
        payload = copy.deepcopy(ARTIFACTS)
        record = next(x for x in payload["artifacts"] if x["source_id"] == "TR.BTK.EHK.5809")
        record["reverify_required"] = False
        with self.assertRaises(gate.GateError):
            gate.validate_registry(payload, SOURCES_PAYLOAD)

    def test_awaiting_record_rejects_fake_hash(self):
        payload = copy.deepcopy(ARTIFACTS)
        payload["artifacts"][0]["sha256"] = "sha256:" + "a" * 64
        with self.assertRaises(gate.GateError):
            gate.validate_registry(payload, SOURCES_PAYLOAD)

    def test_awaiting_record_rejects_false_reverify(self):
        payload = copy.deepcopy(ARTIFACTS)
        record = payload["artifacts"][0]
        record.update(
            artifact_status="awaiting_bytes",
            fetched_at=None,
            size_bytes=None,
            sha256=None,
            change_status="UNKNOWN",
            reverify_required=False,
        )
        with self.assertRaises(gate.GateError):
            gate.validate_registry(payload, SOURCES_PAYLOAD)

    def test_unknown_source_rejected(self):
        payload = copy.deepcopy(ARTIFACTS)
        payload["artifacts"][0]["source_id"] = "TR.UNKNOWN"
        with self.assertRaises(gate.GateError):
            gate.validate_registry(payload, SOURCES_PAYLOAD)

    def test_canonical_url_must_match_source_registry(self):
        payload = copy.deepcopy(ARTIFACTS)
        payload["artifacts"][0]["canonical_url"] = "https://example.invalid/wrong.pdf"
        with self.assertRaises(gate.GateError):
            gate.validate_registry(payload, SOURCES_PAYLOAD)

    def test_pdf_bytes_generate_deterministic_observation(self):
        content = b"%PDF-1.7\nsynthetic-test-artifact\n%%EOF\n"
        expected = "sha256:" + hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "official.pdf"
            path.write_bytes(content)
            source = copy.deepcopy(SOURCES[SOURCE_ID])
            source["content_sha256"] = None
            record = gate.build_observation(
                source,
                path,
                "2026-09-28T20:00:00Z",
                "application/pdf",
            )
        self.assertEqual(record["sha256"], expected)
        self.assertEqual(record["size_bytes"], len(content))
        self.assertEqual(record["change_status"], "HASH_OBSERVED_BIND_REQUIRED")
        self.assertTrue(record["reverify_required"])

    def test_non_pdf_bytes_rejected_for_pdf_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "official.pdf"
            path.write_bytes(b"not a pdf")
            with self.assertRaises(gate.GateError):
                gate.build_observation(
                    SOURCES[SOURCE_ID],
                    path,
                    "2026-09-28T20:00:00Z",
                    "application/pdf",
                )

    def test_matching_known_hash_is_unchanged(self):
        content = b"%PDF-1.7\nknown\n%%EOF\n"
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        source = copy.deepcopy(SOURCES[SOURCE_ID])
        source["content_sha256"] = digest
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "official.pdf"
            path.write_bytes(content)
            record = gate.build_observation(source, path, "2026-09-28T20:00:00Z", "application/pdf")
        self.assertEqual(record["change_status"], "UNCHANGED")
        self.assertFalse(record["reverify_required"])

    def test_changed_known_hash_is_source_changed(self):
        old_content = b"%PDF-1.7\nold\n%%EOF\n"
        new_content = b"%PDF-1.7\nnew\n%%EOF\n"
        source = copy.deepcopy(SOURCES[SOURCE_ID])
        source["content_sha256"] = "sha256:" + hashlib.sha256(old_content).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "official.pdf"
            path.write_bytes(new_content)
            record = gate.build_observation(source, path, "2026-09-28T20:00:00Z", "application/pdf")
        self.assertEqual(record["change_status"], "SOURCE_CHANGED")
        self.assertTrue(record["reverify_required"])

    def test_verified_registry_status_is_derived_from_source_hash(self):
        content = b"%PDF-1.7\nmanifest\n%%EOF\n"
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        sources_payload = copy.deepcopy(SOURCES_PAYLOAD)
        source = next(s for s in sources_payload["sources"] if s["id"] == SOURCE_ID)
        source["content_sha256"] = digest
        payload = {
            "schema_version": 1,
            "artifacts": [{
                "source_id": SOURCE_ID,
                "canonical_url": source["url"],
                "expected_mime_type": "application/pdf",
                "artifact_status": "verified_bytes",
                "fetched_at": "2026-09-28T20:00:00Z",
                "size_bytes": len(content),
                "sha256": digest,
                "change_status": "UNCHANGED",
                "reverify_required": False,
                "notes": "test",
            }],
        }
        self.assertEqual(gate.validate_registry(payload, sources_payload), 1)


if __name__ == "__main__":
    unittest.main()
