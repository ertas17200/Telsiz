#!/usr/bin/env python3
"""Validate the source-grounded Morse data subset."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MORSE = ROOT / "data" / "morse_code.json"
SOURCES = ROOT / "data" / "sources.json"
SIGNAL_RE = re.compile(r"^[.-]{1,5}$")
EXPECTED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    try:
        payload = json.loads(MORSE.read_text(encoding="utf-8"))
        sources_payload = json.loads(SOURCES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"morse: cannot load JSON: {exc}")

    if payload.get("schema_version") != 1:
        fail("morse: schema_version must be 1")
    if payload.get("source_id") != "ITU.R.M1677.1":
        fail("morse: source_id must be ITU.R.M1677.1")

    sources = {s["id"]: s for s in sources_payload.get("sources", [])}
    source = sources.get(payload["source_id"])
    if not source:
        fail("morse: source record is missing")
    if source.get("verification_status") != "verified":
        fail("morse: source must be verified")
    if source.get("source_type") != "official_technical":
        fail("morse: source must be official_technical")
    if source.get("legal_status") != "not_applicable":
        fail("morse: source must not be treated as a Turkish legal permission source")

    chars = payload.get("characters")
    if not isinstance(chars, dict):
        fail("morse: characters must be an object")
    if set(chars) != EXPECTED:
        missing = sorted(EXPECTED - set(chars))
        extra = sorted(set(chars) - EXPECTED)
        fail(f"morse: v1 character set mismatch missing={missing} extra={extra}")
    if not all(isinstance(v, str) and SIGNAL_RE.fullmatch(v) for v in chars.values()):
        fail("morse: every signal must contain 1-5 dot/dash symbols")
    if len(set(chars.values())) != len(chars):
        fail("morse: Morse signals must be unique")

    print(f"PASS: validated {len(chars)} Morse character mappings from {payload['source_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
