"""Receive-only audio contract tests: every hardware-dependent call is mocked."""
import http.client
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import threading
import types
import unittest
import wave

SOURCE = Path(__file__).resolve().parents[1] / 'experimental' / 'ftm400_remote' / 'server.py'
spec = importlib.util.spec_from_file_location('ftm400_audio_preview', SOURCE)
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
TOKEN = 'rx-test-only-unique-never-production-token-123'


def audio_bytes():
    out = io.BytesIO()
    with wave.open(out, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b'\x00\x00' * 32000)
    return out.getvalue()


class RxCaptureTests(unittest.TestCase):
    def test_off_by_default_and_nonwindows_denied(self):
        for dev, platform in (('', 'win32'), ('usb receive input', 'linux'),
                              (' bad\nname', 'win32'), (' leading', 'win32'),
                              ('x' * 257, 'win32')):
            with self.subTest(dev=dev, platform=platform):
                capture = remote.RxCapture(device=dev, platform=platform)
                self.assertFalse(capture.configured)
                with self.assertRaises(remote.RxUnavailable):
                    capture.sample()

    def test_valid_wav_and_fixed_ffmpeg_flags(self):
        commands = []
        def fake_runner(args, **kwargs):
            commands.append((args, kwargs))
            return types.SimpleNamespace(returncode=0, stdout=audio_bytes(), stderr=b'')
        capture = remote.RxCapture(device='Dedicated USB RX Line-In', platform='win32', runner=fake_runner)
        self.assertTrue(capture.configured)
        output = capture.sample()
        self.assertEqual(output, audio_bytes())
        args, opts = commands[0]
        self.assertEqual(args[args.index('-i') + 1], 'audio=Dedicated USB RX Line-In')
        self.assertEqual(args[-1], 'pipe:1')
        self.assertEqual(args[args.index('-t') + 1], '2')
        self.assertEqual(args[args.index('-f') + 1], 'dshow')
        self.assertEqual(args.count('-i'), 1)
        self.assertNotIn('-y', args)
        self.assertFalse(any('rtmp:' in x or 'http:' in x for x in args))
        self.assertEqual(opts['timeout'], 7)
        self.assertEqual(opts['capture_output'], True)
        self.assertEqual(opts['check'], False)

    def test_failure_is_fail_closed(self):
        failures = [
            lambda args, **kw: types.SimpleNamespace(returncode=1, stdout=audio_bytes(), stderr=b'secret environment'),
            lambda args, **kw: types.SimpleNamespace(returncode=0, stdout=b'', stderr=b''),
            lambda args, **kw: types.SimpleNamespace(returncode=0, stdout=b'RIFF' + b'\0' * 100, stderr=b''),
            lambda args, **kw: types.SimpleNamespace(returncode=0, stdout=b'x' * (remote.RX_MAX_WAV_BYTES + 1), stderr=b''),
            lambda args, **kw: (_ for _ in ()).throw(FileNotFoundError('ffmpeg')),
            lambda args, **kw: (_ for _ in ()).throw(subprocess.TimeoutExpired('ffmpeg', 7)),
        ]
        for fail in failures:
            with self.subTest(case=fail):
                capture = remote.RxCapture(device='RX input', platform='win32', runner=fail)
                with self.assertRaises(remote.RxCaptureFailed) as raised:
                    capture.sample()
                self.assertNotIn('secret environment', str(raised.exception))

    def test_busy_fails_without_starting_other_ffmpeg(self):
        calls = []
        rx = remote.RxCapture(device='RX input', platform='win32', runner=lambda *a, **kw: calls.append('called'))
        self.assertTrue(rx._lock.acquire(False))
        try:
            with self.assertRaises(remote.RxBusy):
                rx.sample()
            self.assertEqual(calls, [])
        finally:
            rx._lock.release()

    def test_wrong_pcm_format_denied(self):
        b = io.BytesIO()
        with wave.open(b, 'wb') as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b'\x00' * 200)
        rx = remote.RxCapture(device='RX input', platform='win32', runner=lambda *a, **kw: types.SimpleNamespace(returncode=0, stdout=b.getvalue()))
        with self.assertRaises(remote.RxCaptureFailed):
            rx.sample()


class RxHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audio = audio_bytes()
        cls.runner_calls = []
        def runner(args, **kwargs):
            cls.runner_calls.append(args)
            return types.SimpleNamespace(returncode=0, stdout=cls.audio)
        cls.rx = remote.RxCapture(device='Dedicated USB RX input', platform='win32', runner=runner)
        cls.server = remote.make_server('127.0.0.1', 0, TOKEN, rx_capture=cls.rx)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, endpoint, auth=True, origin=None, host=None):
        headers = {}
        if auth:
            headers['Authorization'] = 'Bearer ' + TOKEN
        if origin is not None:
            headers['Origin'] = origin
        if host is not None:
            headers['Host'] = host
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        conn.request('GET', endpoint, headers=headers)
        response = conn.getresponse()
        code = response.status
        body = response.read()
        mime = response.getheader('Content-Type')
        csp = response.getheader('Content-Security-Policy')
        conn.close()
        return code, body, mime, csp

    def test_unauthorized_has_no_audio_capture(self):
        n = len(self.runner_calls)
        code, body, _, _ = self.request('/api/rx/sample', auth=False)
        self.assertEqual(code, 401)
        self.assertEqual(n, len(self.runner_calls))
        self.assertNotIn(b'RIFF', body)

    def test_untrusted_origin_or_host_no_capture(self):
        n = len(self.runner_calls)
        code, _, _, _ = self.request('/api/rx/sample', origin='https://evil.example')
        self.assertEqual(code, 403)
        code, _, _, _ = self.request('/api/rx/sample', host='not-local.example')
        self.assertEqual(code, 421)
        self.assertEqual(n, len(self.runner_calls))

    def test_audio_endpoint_has_real_binary_wav(self):
        code, data, mime, csp = self.request('/api/rx/sample')
        self.assertEqual(code, 200)
        self.assertEqual(mime, 'audio/wav')
        self.assertEqual(data, self.audio)
        self.assertIn('media-src blob:', csp)

    def test_state_reports_configuration_not_hardware_verified(self):
        code, data, _, _ = self.request('/api/state')
        self.assertEqual(code, 200)
        result = json.loads(data)
        self.assertTrue(result['rx_capture_configured'])
        self.assertFalse(result['rx_capture_verified'])
        self.assertFalse(result['hardware_connected'])
        self.assertFalse(result['rf_transmit_enabled'])
        self.assertEqual(result['ptt'], 'HARDWARE_LOCKED')

    def test_busy_returns_409_without_ffmpeg(self):
        n = len(self.runner_calls)
        self.assertTrue(self.rx._lock.acquire(False))
        try:
            code, body, _, _ = self.request('/api/rx/sample')
            self.assertEqual(code, 409)
            self.assertEqual(json.loads(body)['error'], 'rx_busy')
            self.assertEqual(n, len(self.runner_calls))
        finally:
            self.rx._lock.release()

    def test_default_disabled_returns_503(self):
        disabled = remote.make_server('127.0.0.1', 0, TOKEN, rx_capture=remote.RxCapture(device='', platform='win32'))
        worker = threading.Thread(target=disabled.serve_forever, daemon=True)
        worker.start()
        try:
            c = http.client.HTTPConnection('127.0.0.1', disabled.server_port, timeout=5)
            c.request('GET', '/api/rx/sample', headers={'Authorization': 'Bearer ' + TOKEN})
            resp = c.getresponse()
            self.assertEqual(resp.status, 503)
            self.assertEqual(json.loads(resp.read())['error'], 'rx_not_configured')
            c.close()
        finally:
            disabled.shutdown()
            disabled.server_close()
            worker.join(timeout=3)

    def test_ptt_remains_denied_even_when_rx_enabled(self):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        c.request('POST', '/api/preview', body='{"action":"ptt","enabled":true}', headers={
            'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'})
        resp = c.getresponse()
        self.assertEqual(resp.status, 423)
        resp.read()
        c.close()


if __name__ == '__main__':
    unittest.main()
