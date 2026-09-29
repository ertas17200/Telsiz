#!/usr/bin/env python3
"""Validate the curated SatNOGS satellite/transmitter source layer."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "satellite_transmitters.json"
SOURCES = ROOT / "data" / "sources.json"
EXPECTED_SOURCE = "SATNOGS.DB.SATELLITE_TRANSMITTERS"
EXPECTED_NORAD = {25544, 27607, 39444, 43017}
EXPECTED_TRANSMITTERS = 5
UUID_RE = re.compile(r"^[A-Za-z0-9]{20,24}$")
MODES = {"AFSK", "FM", "USB", "LSB", "BPSK", None}
TYPES = {"Transceiver", "Transponder", "Transmitter"}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"{path.name}: root must be object")
    return value


def main() -> int:
    data = load(DATA)
    sources = {s["id"]: s for s in load(SOURCES)["sources"]}
    source = sources.get(EXPECTED_SOURCE)
    if source is None:
        fail("SatNOGS source record missing")
    if source["verification_status"] != "verified" or source["source_type"] != "community":
        fail("SatNOGS source must be verified community data")
    if data.get("source_id") != EXPECTED_SOURCE:
        fail("source_id mismatch")
    if data.get("authority") != "community_open_data":
        fail("authority must remain community_open_data")
    if data.get("decision_authority") != "technical_reference_only":
        fail("decision_authority must be technical_reference_only")
    if data.get("legal_status") != "UNKNOWN" or data.get("permission_inference") != "PROHIBITED":
        fail("satellite snapshot must never create a legal verdict")
    lic = data.get("license", {})
    if lic.get("spdx_like") != "CC-BY-SA-4.0":
        fail("SatNOGS adapted data must remain CC BY-SA 4.0")
    if "SatNOGS DB contributors" not in lic.get("attribution", ""):
        fail("SatNOGS attribution missing")
    sats = data.get("satellites")
    if not isinstance(sats, list) or {s.get("norad_id") for s in sats} != EXPECTED_NORAD:
        fail("expected curated NORAD set mismatch")

    seen_uuid: set[str] = set()
    transmitter_count = 0
    aliases: set[str] = set()
    for sat in sats:
        norad = sat["norad_id"]
        expected_url = f"https://db.satnogs.org/satellite/{norad}/"
        if sat.get("source_url") != expected_url:
            fail(f"{norad}: source_url mismatch")
        names = [sat.get("name"), *sat.get("aliases", [])]
        for name in names:
            key = str(name).upper()
            if key in aliases:
                fail(f"duplicate satellite alias/name: {name}")
            aliases.add(key)
        txs = sat.get("transmitters")
        if not isinstance(txs, list) or not txs:
            fail(f"{norad}: transmitter list required")
        for tx in txs:
            transmitter_count += 1
            uuid = tx.get("uuid")
            if not isinstance(uuid, str) or not UUID_RE.fullmatch(uuid) or uuid in seen_uuid:
                fail(f"{norad}: invalid/duplicate transmitter UUID")
            seen_uuid.add(uuid)
            if tx.get("type") not in TYPES:
                fail(f"{uuid}: unsupported transmitter type")
            for side in ("downlink", "uplink"):
                part = tx.get(side)
                if not isinstance(part, dict):
                    fail(f"{uuid}: {side} must be object")
                low, high, mode = part.get("low_hz"), part.get("high_hz"), part.get("mode")
                if low is not None and (not isinstance(low, int) or isinstance(low, bool) or low <= 0):
                    fail(f"{uuid}: invalid {side} low_hz")
                if high is not None and (low is None or not isinstance(high, int) or high < low):
                    fail(f"{uuid}: invalid {side} high_hz")
                if mode not in MODES:
                    fail(f"{uuid}: unexpected {side} mode")
            if tx.get("baud") is not None and (not isinstance(tx["baud"], int) or tx["baud"] <= 0):
                fail(f"{uuid}: invalid baud")
            if tx.get("access_tone_hz") is not None and tx["access_tone_hz"] <= 0:
                fail(f"{uuid}: invalid access tone")
            if not isinstance(tx.get("source_locator"), str) or not tx["source_locator"]:
                fail(f"{uuid}: source_locator required")

    if transmitter_count != EXPECTED_TRANSMITTERS:
        fail(f"expected {EXPECTED_TRANSMITTERS} selected transmitter/transponder records, got {transmitter_count}")

    by_norad = {s["norad_id"]: s for s in sats}
    iss = by_norad[25544]["transmitters"][0]
    if (iss["downlink"]["low_hz"], iss["uplink"]["low_hz"], iss["baud"]) != (145825000, 145825000, 1200):
        fail("ISS APRS key facts drifted")
    so50 = by_norad[27607]["transmitters"][0]
    if (so50["uplink"]["low_hz"], so50["downlink"]["low_hz"], so50["access_tone_hz"]) != (145850000, 436795000, 67.0):
        fail("SO-50 key facts drifted")
    ao73 = by_norad[39444]["transmitters"][0]
    if (ao73["uplink"]["low_hz"], ao73["uplink"]["high_hz"], ao73["downlink"]["low_hz"], ao73["downlink"]["high_hz"], ao73["inverted"]) != (435130000, 435150000, 145950000, 145970000, True):
        fail("AO-73 linear transponder key facts drifted")
    ao91 = by_norad[43017]["transmitters"][0]
    if (ao91["uplink"]["low_hz"], ao91["downlink"]["low_hz"], ao91["access_tone_hz"]) != (435250000, 145960000, None):
        fail("AO-91 key facts drifted")

    print(f"PASS: validated {len(sats)} satellite(s), {transmitter_count} selected SatNOGS transmitter/transponder record(s); legal permission inference disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
