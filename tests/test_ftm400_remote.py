"""Fail-closed regression and HTTP tests for the FTM-400 UI preview."""
import http.client
import importlib.util
import json
import threading
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "experimental" / "ftm400_remote" / "server.py"
spec = importlib.util.spec_from_file_location("ftm400_remote_server", SOURCE)
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
TOKEN = "test-only-unique-not-a-production-secret-123"


class ModelTests(unittest.TestCase):
    def test_every_ftm400_variant(self):
        for model in ("FTM-400DR", "FTM-400DE", "FTM-400XDR", "FTM-400XDE"):
            with self.subTest(model=model):
                radio = remote.PreviewRadio(model)
                self.assertEqual(radio.snapshot()["model"], model)
                self.assertEqual(radio.snapshot()["rf_transmit_enabled"], False)

    def test_family_separation(self):
        self.assertEqual(remote.PreviewRadio("FTM-400DE").snapshot()["firmware_family"], "DR/DE")
        self.assertEqual(remote.PreviewRadio("FTM-400XDE").snapshot()["firmware_family"], "XDR/XDE")

    def test_ambiguous_or_non_ftm400_rejected(self):
        for value in ("FTM-400", "FTM-500", "", None, "ftm-400dr"):
            with self.subTest(value=value), self.assertRaises(remote.InvalidCommand):
                remote.PreviewRadio(value)

    def test_preview_only_and_ptt_locked(self):
        radio = remote.PreviewRadio()
        state = radio.apply({"action": "preview_frequency", "frequency_mhz": 145.5})
        self.assertEqual(state["frequency_preview_mhz"], 145.5)
        self.assertFalse(state["hardware_connected"])
        for operation in ("ptt", "tx", "transmit", "mic", "audio", "screen"):
            with self.subTest(operation=operation), self.assertRaises(remote.TransmitHeld):
                radio.apply({"action": operation, "enabled": True})

    def test_model_change_clears_stale_previews(self):
        radio = remote.PreviewRadio()
        radio.apply({"action": "preview_channel", "channel": 15})
        state = radio.apply({"action": "select_model", "model": "FTM-400XDE"})
        self.assertIsNone(state["channel_preview"])

    def test_strict_commands_and_ranges(self):
        radio = remote.PreviewRadio()
        bad = [None, [], {}, {"action": "preview_channel", "channel": True},
               {"action": "preview_channel", "channel": 0},
               {"action": "preview_channel", "channel": 1000},
               {"action": "preview_volume", "volume": 101},
               {"action": "preview_frequency", "frequency_mhz": float("nan")},
               {"action": "preview_frequency", "frequency_mhz": 1e999},
               {"action": "preview_frequency", "frequency_mhz": "145.5"},
               {"action": "select_model", "model": "FTM-400DR", "secret": "unexpected"}]
        for item in bad:
            with self.subTest(item=item), self.assertRaises(remote.InvalidCommand):
                radio.apply(item)

    def test_boundaries(self):
        radio = remote.PreviewRadio()
        self.assertEqual(radio.apply({"action": "preview_frequency", "frequency_mhz": 1})["frequency_preview_mhz"], 1)
        self.assertEqual(radio.apply({"action": "preview_frequency", "frequency_mhz": 1000})["frequency_preview_mhz"], 1000)
        self.assertEqual(radio.apply({"action": "preview_volume", "volume": 0})["volume_preview"], 0)
        self.assertEqual(radio.apply({"action": "preview_channel", "channel": 999})["channel_preview"], 999)

    def test_duplicate_json_key_denied(self):
        with self.assertRaises(remote.InvalidCommand):
            json.loads('{"action":"preview_channel","action":"ptt"}', object_pairs_hook=remote._unique_pairs)

    def test_untrusted_bind_denied(self):
        for host in ("0.0.0.0", "::1", "localhost"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                remote.make_server(host, 0, TOKEN)

    def test_short_token_denied(self):
        with self.assertRaises(ValueError):
            remote.make_server("127.0.0.1", 0, "weak")


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = remote.make_server("127.0.0.1", 0, TOKEN)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def req(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        conn.request(method, path, body=body, headers=headers or {})
        result = conn.getresponse()
        code, data, csp = result.status, result.read(), result.getheader("Content-Security-Policy")
        conn.close()
        return code, data, csp

    def test_asset_served_with_csp(self):
        code, body, csp = self.req("GET", "/")
        self.assertEqual(code, 200)
        self.assertIn(b"FTM-400 Remote", body)
        self.assertIn("default-src 'none'", csp)

    def test_unauthenticated_state_denied(self):
        code, _, _ = self.req("GET", "/api/state")
        self.assertEqual(code, 401)

    def test_authenticated_state_and_readback(self):
        hdr = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}
        code, data, _ = self.req("POST", "/api/preview", json.dumps({"action": "select_model", "model": "FTM-400XDR"}), hdr)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(data)["firmware_family"], "XDR/XDE")
        code, data, _ = self.req("GET", "/api/state", headers=hdr)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(data)["model"], "FTM-400XDR")
        self.assertFalse(json.loads(data)["rf_transmit_enabled"])

    def test_http_ptt_rejected(self):
        hdr = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}
        code, _, _ = self.req("POST", "/api/preview", '{"action":"ptt","enabled":true}', hdr)
        self.assertEqual(code, 423)

    def test_http_wrong_origin_and_duplicate_keys(self):
        hdr = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json", "Origin": "https://evil.example"}
        code, _, _ = self.req("POST", "/api/preview", '{}', hdr)
        self.assertEqual(code, 403)
        hdr.pop("Origin")
        code, _, _ = self.req("POST", "/api/preview", '{"action":"x","action":"ptt"}', hdr)
        self.assertEqual(code, 400)

    def test_dns_rebinding_host_is_rejected(self):
        for method, path, body in (
            ("GET", "/", None),
            ("GET", "/api/state", None),
            ("POST", "/api/preview", '{"action":"preview_volume","volume":1}'),
        ):
            with self.subTest(method=method, path=path):
                headers = {"Host": "untrusted.example", "Authorization": "Bearer " + TOKEN,
                           "Content-Type": "application/json"}
                code, _, _ = self.req(method, path, body=body, headers=headers)
                self.assertEqual(code, 421, "untrusted host must be refused")

    def test_http_oversized_request_rejected(self):
        hdr = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}
        code, _, _ = self.req("POST", "/api/preview", " " * 1030, hdr)
        self.assertEqual(code, 413)


if __name__ == "__main__":
    unittest.main()
