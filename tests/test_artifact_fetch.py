import copy
import hashlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "fetch_official_artifact", SCRIPTS / "fetch_official_artifact.py"
)
fetcher = importlib.util.module_from_spec(spec)
sys.modules["fetch_official_artifact"] = fetcher
assert spec.loader is not None
spec.loader.exec_module(fetcher)

SOURCES_PAYLOAD = json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))
ARTIFACTS_PAYLOAD = json.loads((ROOT / "data" / "artifacts.json").read_text("utf-8"))
SOURCE_ID = "TR.BTK.FTM.TECH.2022-IK-SYD-245"
SOURCE = next(x for x in SOURCES_PAYLOAD["sources"] if x["id"] == SOURCE_ID)
ARTIFACT = next(x for x in ARTIFACTS_PAYLOAD["artifacts"] if x["source_id"] == SOURCE_ID)


class FakeHeaders(dict):
    def get_content_type(self):
        return str(self.get("Content-Type", "")).split(";", 1)[0].strip().lower()


class FakeResponse:
    def __init__(self, body, *, url=None, content_type="application/pdf", content_length=True, status=200):
        self._stream = io.BytesIO(body)
        self.status = status
        self._url = url or SOURCE["url"]
        self.headers = FakeHeaders({"Content-Type": content_type})
        if content_length:
            self.headers["Content-Length"] = str(len(body))

    def geturl(self):
        return self._url

    def read(self, size=-1):
        return self._stream.read(size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class ArtifactFetchTests(unittest.TestCase):
    def test_suffix_is_derived_from_expected_mime(self):
        self.assertEqual(fetcher.suffix_for_mime("application/pdf"), ".pdf")
        self.assertEqual(fetcher.suffix_for_mime("text/html"), ".html")
        self.assertEqual(fetcher.suffix_for_mime("application/json"), ".json")
        with self.assertRaises(fetcher.gate.GateError):
            fetcher.suffix_for_mime("application/octet-stream")

    def test_artifact_map_rejects_duplicates(self):
        payload = {"artifacts": [ARTIFACT, ARTIFACT]}
        with self.assertRaises(fetcher.gate.GateError):
            fetcher.artifact_map(payload)

    def test_canonical_url_must_be_https(self):
        source = dict(SOURCE)
        source["url"] = "http://www.btk.gov.tr/file.pdf"
        artifact = dict(ARTIFACT)
        artifact["canonical_url"] = source["url"]
        with self.assertRaises(fetcher.gate.GateError):
            fetcher.fetch_registered_artifact(source, artifact, Path("/tmp/never-written"))

    @patch("fetch_official_artifact.urlopen")
    def test_fetch_writes_exact_pdf_bytes(self, mocked):
        body = b"%PDF-1.7\nbyte-evidence\n%%EOF\n"
        mocked.return_value = FakeResponse(body)
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.pdf"
            meta = fetcher.fetch_registered_artifact(SOURCE, ARTIFACT, path)
            self.assertEqual(path.read_bytes(), body)
        self.assertEqual(meta["downloaded_bytes"], len(body))
        self.assertEqual(meta["http_status"], 200)
        self.assertEqual(meta["http_content_type"], "application/pdf")

    @patch("fetch_official_artifact.urlopen")
    def test_non_200_http_status_rejected(self, mocked):
        mocked.return_value = FakeResponse(b"%PDF-1.7\nX\n", status=206)
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(fetcher.gate.GateError):
                fetcher.fetch_registered_artifact(
                    SOURCE, ARTIFACT, Path(tmp) / "artifact.pdf"
                )

    @patch("fetch_official_artifact.urlopen")
    def test_cross_origin_redirect_rejected(self, mocked):
        mocked.return_value = FakeResponse(
            b"%PDF-1.7\nX\n",
            url="https://example.invalid/file.pdf",
        )
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(fetcher.gate.GateError):
                fetcher.fetch_registered_artifact(
                    SOURCE, ARTIFACT, Path(tmp) / "artifact.pdf"
                )

    @patch("fetch_official_artifact.urlopen")
    def test_wrong_http_content_type_rejected(self, mocked):
        mocked.return_value = FakeResponse(
            b"%PDF-1.7\nX\n",
            content_type="text/html",
        )
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(fetcher.gate.GateError):
                fetcher.fetch_registered_artifact(
                    SOURCE, ARTIFACT, Path(tmp) / "artifact.pdf"
                )

    @patch("fetch_official_artifact.urlopen")
    def test_declared_oversize_rejected_before_body(self, mocked):
        response = FakeResponse(b"%PDF-1.7\nX\n")
        response.headers["Content-Length"] = "101"
        mocked.return_value = response
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(fetcher.gate.GateError):
                fetcher.fetch_registered_artifact(
                    SOURCE,
                    ARTIFACT,
                    Path(tmp) / "artifact.pdf",
                    max_bytes=100,
                )

    @patch("fetch_official_artifact.urlopen")
    def test_stream_oversize_rejected_without_content_length(self, mocked):
        body = b"%PDF-1.7\n" + b"x" * 100
        mocked.return_value = FakeResponse(body, content_length=False)
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(fetcher.gate.GateError):
                fetcher.fetch_registered_artifact(
                    SOURCE,
                    ARTIFACT,
                    Path(tmp) / "artifact.pdf",
                    max_bytes=50,
                )

    @patch("fetch_official_artifact.urlopen")
    def test_observation_is_hash_evidence_but_not_auto_binding(self, mocked):
        body = b"%PDF-1.7\ncanonical-test\n%%EOF\n"
        mocked.return_value = FakeResponse(body)

        sources_payload = copy.deepcopy(SOURCES_PAYLOAD)
        source = next(x for x in sources_payload["sources"] if x["id"] == SOURCE_ID)
        source["content_sha256"] = None

        artifacts_payload = copy.deepcopy(ARTIFACTS_PAYLOAD)
        artifact = next(x for x in artifacts_payload["artifacts"] if x["source_id"] == SOURCE_ID)
        artifact.update(
            artifact_status="awaiting_bytes",
            fetched_at=None,
            size_bytes=None,
            sha256=None,
            change_status="UNKNOWN",
            reverify_required=True,
        )

        def fake_load(path):
            if path == fetcher.gate.SOURCES:
                return sources_payload
            if path == fetcher.gate.ARTIFACTS:
                return artifacts_payload
            raise AssertionError(f"unexpected path: {path}")

        with patch.object(fetcher.gate, "load_json", side_effect=fake_load):
            observation = fetcher.observe_source(
                SOURCE_ID,
                "2026-09-29T10:30:00Z",
            )

        expected = "sha256:" + hashlib.sha256(body).hexdigest()
        self.assertEqual(observation["sha256"], expected)
        self.assertEqual(observation["size_bytes"], len(body))
        self.assertEqual(observation["retrieval"]["http_status"], 200)
        self.assertEqual(observation["change_status"], "HASH_OBSERVED_BIND_REQUIRED")
        self.assertTrue(observation["reverify_required"])
        self.assertEqual(
            observation["binding_action"],
            "REVIEW_REQUIRED_NO_AUTOMATIC_REGISTRY_MUTATION",
        )


    @patch("fetch_official_artifact.urlopen")
    def test_pending_html_source_observation_uses_html_artifact(self, mocked):
        source_id = "TR.BTK.EHK.5809"
        source = next(x for x in SOURCES_PAYLOAD["sources"] if x["id"] == source_id)
        artifact = next(x for x in ARTIFACTS_PAYLOAD["artifacts"] if x["source_id"] == source_id)
        body = b"<!doctype html><html><body>official</body></html>"
        mocked.return_value = FakeResponse(
            body,
            url=source["url"],
            content_type="text/html",
        )

        def fake_load(path):
            if path == fetcher.gate.SOURCES:
                return SOURCES_PAYLOAD
            if path == fetcher.gate.ARTIFACTS:
                return ARTIFACTS_PAYLOAD
            raise AssertionError(f"unexpected path: {path}")

        with patch.object(fetcher.gate, "load_json", side_effect=fake_load):
            observation = fetcher.observe_source(
                source_id,
                "2026-09-29T18:40:00Z",
            )

        self.assertEqual(observation["source_id"], source_id)
        self.assertEqual(observation["expected_mime_type"], "text/html")
        self.assertEqual(observation["observed_mime_type"], "text/html")
        self.assertEqual(observation["retrieval"]["http_status"], 200)
        self.assertEqual(observation["retrieval"]["http_content_type"], "text/html")
        self.assertEqual(observation["change_status"], "HASH_OBSERVED_BIND_REQUIRED")
        self.assertTrue(observation["reverify_required"])
        self.assertEqual(
            observation["binding_action"],
            "REVIEW_REQUIRED_NO_AUTOMATIC_REGISTRY_MUTATION",
        )


if __name__ == "__main__":
    unittest.main()
