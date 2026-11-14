#!/usr/bin/env python3
"""Loopback-only, receive/transmit-disconnected FTM-400 remote-control UI prototype.

No GPIO, serial, DATA-port, CAT, microphone TX or RF adapter is implemented.
Optional, explicitly configured Windows DirectShow RX-only PCM audio clips are supported.
All controls in this module are previews, never commands to a physical radio.
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
import wave
import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MODELS = {
    "FTM-400DR": "DR/DE",
    "FTM-400DE": "DR/DE",
    "FTM-400XDR": "XDR/XDE",
    "FTM-400XDE": "XDR/XDE",
}
TOKEN_ENV = "FTM400_REMOTE_TOKEN"
ROOT = Path(__file__).resolve().parent
MAX_BODY = 1024
RX_DEVICE_ENV = "FTM400_RX_AUDIO_DEVICE"
RX_MAX_WAV_BYTES = 131072
RX_DURATION_SECONDS = 2


class InvalidCommand(ValueError):
    pass


class TransmitHeld(InvalidCommand):
    pass


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise InvalidCommand("duplicate JSON key")
        value[key] = item
    return value


class RxUnavailable(Exception):
    """Receive audio requires explicit Windows device configuration."""


class RxBusy(Exception):
    """Only one audio capture may run at once."""


class RxCaptureFailed(Exception):
    """The selected local audio input did not return a valid bounded WAV."""


class RxCapture:
    """Opt-in, two-second receiver audio capture. No TX-side calls or ports."""

    def __init__(self, device=None, platform=None, runner=None, executable="ffmpeg"):
        self.device = os.environ.get(RX_DEVICE_ENV, "") if device is None else device
        self.platform = sys.platform if platform is None else platform
        self.runner = subprocess.run if runner is None else runner
        self.executable = executable
        self._lock = threading.Lock()

    @property
    def configured(self):
        return (self.platform == "win32" and isinstance(self.device, str)
                and 1 <= len(self.device) <= 256 and not any(ord(c) < 32 for c in self.device)
                and self.device == self.device.strip())

    def sample(self):
        if not self.configured:
            raise RxUnavailable("receive audio is not configured for Windows")
        if not self._lock.acquire(blocking=False):
            raise RxBusy("another receive sample is in progress")
        try:
            # User-configured DirectShow INPUT only. No shell, PTT, radio control,
            # microphone output, network output, or permanent recording.
            args = [self.executable, "-nostdin", "-hide_banner", "-loglevel", "error",
                    "-f", "dshow", "-i", "audio=" + self.device,
                    "-t", str(RX_DURATION_SECONDS), "-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "pcm_s16le", "-f", "wav", "-fs", str(RX_MAX_WAV_BYTES), "pipe:1"]
            try:
                result = self.runner(args, capture_output=True, timeout=7, check=False)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise RxCaptureFailed("receive capture failed or timed out") from exc
            if result.returncode != 0 or not isinstance(result.stdout, bytes):
                raise RxCaptureFailed("receive capture failed")
            data = result.stdout
            if not (44 <= len(data) <= RX_MAX_WAV_BYTES and data[:4] == b"RIFF"
                    and data[8:12] == b"WAVE"):
                raise RxCaptureFailed("invalid receive WAV")
            try:
                with wave.open(io.BytesIO(data), "rb") as clip:
                    if (clip.getnchannels(), clip.getframerate(), clip.getsampwidth(),
                            clip.getcomptype()) != (1, 16000, 2, "NONE"):
                        raise RxCaptureFailed("unexpected receive WAV format")
                    if not clip.readframes(1):
                        raise RxCaptureFailed("empty receive WAV")
            except (EOFError, wave.Error) as exc:
                raise RxCaptureFailed("malformed receive WAV") from exc
            return data
        finally:
            self._lock.release()


class PreviewRadio:
    """Version-independent UI state. No hardware I/O by design."""

    def __init__(self, model: str = "FTM-400DR") -> None:
        if model not in MODELS:
            raise InvalidCommand("unsupported radio model")
        self._lock = threading.RLock()
        self.model = model
        self.frequency_mhz: float | None = None
        self.channel: int | None = None
        self.volume: int | None = None

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "model": self.model,
                "firmware_family": MODELS[self.model],
                "frequency_preview_mhz": self.frequency_mhz,
                "channel_preview": self.channel,
                "volume_preview": self.volume,
                "hardware_connected": False,
                "microphone": "UNAVAILABLE",
                "speaker": "UNAVAILABLE",
                "screen": "UNAVAILABLE",
                "ptt": "HARDWARE_LOCKED",
                "rf_transmit_enabled": False,
                "status": "SIMULATION_ONLY",
            }

    def apply(self, command: object) -> dict:
        if type(command) is not dict:
            raise InvalidCommand("command must be a JSON object")
        action = command.get("action")
        if action in ("ptt", "tx", "transmit", "mic", "audio", "screen"):
            raise TransmitHeld("physical radio operations are disabled pending hardware verification")
        keys = {
            "select_model": ("action", "model"),
            "preview_frequency": ("action", "frequency_mhz"),
            "preview_channel": ("action", "channel"),
            "preview_volume": ("action", "volume"),
        }
        if not isinstance(action, str) or action not in keys:
            raise InvalidCommand("unsupported command")
        if set(command) != set(keys[action]):
            raise InvalidCommand("unexpected or missing command fields")
        with self._lock:
            if action == "select_model":
                model = command["model"]
                if type(model) is not str or model not in MODELS:
                    raise InvalidCommand("unsupported radio model")
                if model != self.model:
                    self.model = model
                    self.frequency_mhz = self.channel = self.volume = None
            elif action == "preview_frequency":
                frequency = command["frequency_mhz"]
                if type(frequency) not in (float, int) or not 1 <= frequency <= 1000:
                    raise InvalidCommand("preview frequency must be a finite number from 1 to 1000 MHz")
                self.frequency_mhz = round(frequency, 5)
            elif action == "preview_channel":
                channel = command["channel"]
                if type(channel) is not int or not 1 <= channel <= 999:
                    raise InvalidCommand("preview channel must be an integer from 1 to 999")
                self.channel = channel
            elif action == "preview_volume":
                volume = command["volume"]
                if type(volume) is not int or not 0 <= volume <= 100:
                    raise InvalidCommand("preview volume must be an integer from 0 to 100")
                self.volume = volume
            return self.snapshot()


def make_server(host: str, port: int, token: str, radio: PreviewRadio | None = None, rx_capture: RxCapture | None = None) -> ThreadingHTTPServer:
    if host != "127.0.0.1":
        raise ValueError("only literal IPv4 loopback 127.0.0.1 may be bound")
    if not isinstance(token, str) or len(token) < 24 or any(ch.isspace() for ch in token):
        raise ValueError("set FTM400_REMOTE_TOKEN to a non-whitespace token of at least 24 characters")
    target = radio if radio is not None else PreviewRadio()
    rx = rx_capture if rx_capture is not None else RxCapture()

    class Handler(BaseHTTPRequestHandler):
        server_version = "FTM400Preview/0.1"

        def log_message(self, fmt: str, *args: object) -> None:
            return  # Never record URL, authorization token or body.

        def _send(self, code: int, body: bytes, mime: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; media-src blob:; base-uri 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, result: dict) -> None:
            self._send(code, json.dumps(result, allow_nan=False, separators=(",", ":")).encode(), "application/json; charset=utf-8")

        def _authorized(self) -> bool:
            got = self.headers.get("Authorization", "")
            return hmac.compare_digest(got, "Bearer " + token)

        def _check_host(self) -> bool:
            # A strict loopback Host boundary blocks browser DNS rebinding to this
            # development server. Duplicate or missing Host headers also fail closed.
            hosts = self.headers.get_all("Host", [])
            return len(hosts) == 1 and hosts[0] == f"127.0.0.1:{self.server.server_port}"

        def _check_origin(self) -> bool:
            origin = self.headers.get("Origin")
            return origin is None or origin == f"http://127.0.0.1:{self.server.server_port}"

        def do_GET(self) -> None:
            if not self._check_host():
                self._json(421, {"error": "untrusted_host"})
                return
            assets = {"/": ("index.html", "text/html; charset=utf-8"), "/client.js": ("client.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8")}
            if self.path in assets:
                filename, mime = assets[self.path]
                self._send(200, (ROOT / filename).read_bytes(), mime)
                return
            if self.path == "/api/rx/sample":
                if not self._authorized():
                    self._json(401, {"error": "unauthorized"})
                elif not self._check_origin():
                    self._json(403, {"error": "origin_denied"})
                else:
                    try:
                        self._send(200, rx.sample(), "audio/wav")
                    except RxUnavailable:
                        self._json(503, {"error": "rx_not_configured"})
                    except RxBusy:
                        self._json(409, {"error": "rx_busy"})
                    except RxCaptureFailed:
                        self._json(503, {"error": "rx_capture_failed"})
                return
            if self.path != "/api/state":
                self._json(404, {"error": "not_found"})
            elif not self._authorized():
                self._json(401, {"error": "unauthorized"})
            else:
                state = target.snapshot()
                state["rx_capture_configured"] = rx.configured
                state["rx_capture_verified"] = False  # No hardware readback in this software.
                self._json(200, state)

        def do_POST(self) -> None:
            if not self._check_host():
                self._json(421, {"error": "untrusted_host"})
                return
            if self.path != "/api/preview":
                self._json(404, {"error": "not_found"})
                return
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            if not self._check_origin():
                self._json(403, {"error": "origin_denied"})
                return
            if self.headers.get("Content-Type") != "application/json":
                self._json(415, {"error": "json_content_type_required"})
                return
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_BODY:
                self._json(413, {"error": "invalid_body_size"})
                return
            raw = self.rfile.read(length)
            try:
                data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                                  parse_constant=lambda _: (_ for _ in ()).throw(InvalidCommand("non-finite JSON number")))
                result = target.apply(data)
            except (UnicodeDecodeError, ValueError, TypeError) as exc:
                self._json(423 if isinstance(exc, TransmitHeld) else 400, {"error": str(exc)})
                return
            self._json(200, result)

    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="FTM-400 all-variant UI preview, no radio I/O")
    parser.add_argument("--host", default="127.0.0.1", choices=["127.0.0.1"])
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    token = os.environ.get(TOKEN_ENV, "")
    server = make_server(args.host, args.port, token)
    print(f"FTM400 preview: http://{args.host}:{server.server_port}/ — radio TX disabled", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
