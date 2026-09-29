import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location(
        "probe_official_artifact", ROOT / "scripts" / "probe_official_artifact.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_official_artifact"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


probe = load_module()


class FakeHeaders:
    def __init__(self, content_type):
        self.content_type = content_type

    def get_content_type(self):
        return self.content_type


class FakeResponse:
    def __init__(self, body, url, status=200, content_type="application/pdf"):
        self.body = body
        self.url = url
        self.status = status
        self.headers = FakeHeaders(content_type)
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, size=-1):
        if self.offset >= len(self.body):
            return b""
        if size < 0:
            size = len(self.body) - self.offset
        chunk = self.body[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


class ProbeTests(unittest.TestCase):
    URL = "https://www.btk.gov.tr/uploads/pages/ftm-teknik-olcutler-ek-5.pdf"

    def run_fetch(self, response):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "artifact.pdf"
            with mock.patch.object(probe.urllib.request, "urlopen", return_value=response):
                result = probe.fetch(self.URL, out, 1)
            data = out.read_bytes()
        return result, data

    def test_valid_pdf_produces_hash_and_size(self):
        body = b"%PDF-1.7\nsynthetic\n%%EOF\n"
        result, data = self.run_fetch(FakeResponse(body, self.URL))
        self.assertEqual(data, body)
        self.assertEqual(result["size_bytes"], len(body))
        self.assertEqual(result["sha256"], "sha256:" + hashlib.sha256(body).hexdigest())
        self.assertEqual(result["acquisition_status"], "BYTE_ARTIFACT_OBSERVED")

    def test_redirect_is_rejected(self):
        with self.assertRaises(RuntimeError):
            self.run_fetch(FakeResponse(b"%PDF-1.7\n", self.URL + "?redirected=1"))

    def test_non_pdf_signature_is_rejected(self):
        with self.assertRaises(RuntimeError):
            self.run_fetch(FakeResponse(b"<html>blocked</html>", self.URL))

    def test_unexpected_content_type_is_rejected(self):
        with self.assertRaises(RuntimeError):
            self.run_fetch(FakeResponse(b"%PDF-1.7\n", self.URL, content_type="text/html"))

    def test_non_200_is_rejected(self):
        with self.assertRaises(RuntimeError):
            self.run_fetch(FakeResponse(b"%PDF-1.7\n", self.URL, status=403))


if __name__ == "__main__":
    unittest.main()
