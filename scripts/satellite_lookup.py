#!/usr/bin/env python3
"""Fail-closed lookup for the curated SatNOGS satellite transmitter snapshot."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "satellite_transmitters.json"


def load_registry() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", value.upper())


def alias_map(registry: dict) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for sat in registry["satellites"]:
        values = [sat["name"], *sat["aliases"], str(sat["norad_id"])]
        for value in values:
            key = _key(value)
            if key in result and result[key]["norad_id"] != sat["norad_id"]:
                raise ValueError(f"duplicate normalized satellite alias: {value}")
            result[key] = sat
    return result


def lookup(query: str, registry: dict | None = None) -> dict:
    registry = registry or load_registry()
    sat = alias_map(registry).get(_key(query))
    if sat is None:
        return {
            "status": "not_found",
            "query": query,
            "legal_status": "UNKNOWN",
            "permission_inference": "PROHIBITED",
            "matches": [],
        }
    return {
        "status": "exact",
        "query": query,
        "legal_status": "UNKNOWN",
        "permission_inference": "PROHIBITED",
        "matches": [sat],
    }


def find_mentions(question: str, registry: dict | None = None) -> list[dict]:
    registry = registry or load_registry()
    found: list[dict] = []
    seen: set[int] = set()
    upper = question.upper()
    for sat in registry["satellites"]:
        candidates = [sat["name"], *sat["aliases"], str(sat["norad_id"])]
        for candidate in sorted(candidates, key=len, reverse=True):
            pattern = r"(?<![A-Z0-9])" + re.escape(candidate.upper()) + r"(?![A-Z0-9])"
            if re.search(pattern, upper):
                if sat["norad_id"] not in seen:
                    found.append(sat)
                    seen.add(sat["norad_id"])
                break
    return found


def _mhz(hz: int | None) -> str:
    if hz is None:
        return "—"
    value = hz / 1_000_000
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return f"{text} MHz"


def _side(part: dict) -> str:
    if part["low_hz"] is None:
        return "—"
    freq = _mhz(part["low_hz"])
    if part["high_hz"] is not None:
        freq = f"{_mhz(part['low_hz']).removesuffix(' MHz')}–{_mhz(part['high_hz'])}"
    return f"{freq} {part['mode'] or ''}".strip()


def describe_transmitter(tx: dict) -> str:
    pieces = [tx["description"], f"uplink {_side(tx['uplink'])}", f"downlink {_side(tx['downlink'])}"]
    if tx["baud"] is not None:
        pieces.append(f"{tx['baud']} baud")
    if tx["access_tone_hz"] is not None:
        pieces.append(f"CTCSS {tx['access_tone_hz']:g} Hz")
    if tx["inverted"] is True:
        pieces.append("inverting")
    if tx["iaru_coordination"]:
        pieces.append(tx["iaru_coordination"])
    return "; ".join(pieces)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("satellite")
    args = p.parse_args()
    result = lookup(args.satellite)
    if result["status"] == "not_found":
        print(f"{args.satellite}: curated snapshot'ta tam eşleşme yok; tahmin edilmedi.")
        return 1
    sat = result["matches"][0]
    print(f"{sat['name']} ({', '.join(sat['aliases']) or 'alias yok'}; NORAD {sat['norad_id']})")
    for tx in sat["transmitters"]:
        print(f"- {describe_transmitter(tx)}")
    print("LEGAL_STATUS=UNKNOWN")
    print("PERMISSION_INFERENCE=PROHIBITED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
