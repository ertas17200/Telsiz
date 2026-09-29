#!/usr/bin/env python3
"""Validate the raw visual transcription of the official BTK amateur table.

This validator proves transcription integrity only. It does not promote the
semantic frequency table to complete. The canonical artifact SHA-256 is now
bound separately and must match the raw transcription metadata.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "btk_amateur_table_raw.json"
EMISSIONS = ROOT / "data" / "btk_emission_types.json"

EXPECTED_SOURCE = "TR.BTK.FTM.TECH.2022-IK-SYD-245"
EXPECTED_ROWS = 33
EXPECTED_EMISSION_DEFINITIONS = 24
EXPECTED_ARTIFACT_SHA256 = "sha256:eff832fc30df1adf60e4a8c514a6069154d526d3ab88ae803b51a5536d103db0"
EXPECTED_PROMOTION_STATUS = "HOLD_SOURCE_CONFLICTS_AND_SEMANTIC_MODEL"
ALLOWED_UNITS = {"kHz", "MHz", "GHz"}
ALLOWED_CLASSES = {"A", "B", "C"}
ALLOWED_PAGES = {"41/47", "42/47", "43/47", "44/47", "45/47"}
KNOWN_UNDEFINED_EMISSIONS = {"A3J", "J2C"}
EXPECTED_CONFLICTS = {
    "TR-BTK-NUMBERING-001",
    "TR-BTK-EMISSION-001",
    "TR-BTK-UNIT-001",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot load {path.name}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.name}: root must be an object")
    return value


def find_row(rows: list[dict], low: float, high: float, unit: str) -> dict:
    for row in rows:
        if row.get("frequency_min") == low and row.get("frequency_max") == high and row.get("unit") == unit:
            return row
    fail(f"missing expected row {low}-{high} {unit}")


def validate_payloads(raw: dict, emission_map: dict) -> None:
    if raw.get("schema_version") != 1 or emission_map.get("schema_version") != 1:
        fail("schema_version must be 1")
    if raw.get("source_id") != EXPECTED_SOURCE or emission_map.get("source_id") != EXPECTED_SOURCE:
        fail("source_id mismatch")
    if raw.get("source_rows_counted") != EXPECTED_ROWS:
        fail(f"source_rows_counted must be {EXPECTED_ROWS}")
    if raw.get("transcription_status") != "visual_official_source_complete_rows":
        fail("unexpected transcription_status")
    if raw.get("artifact_sha256") != EXPECTED_ARTIFACT_SHA256:
        fail("raw transcription artifact_sha256 must match the bound canonical baseline")
    if raw.get("semantic_promotion_status") != EXPECTED_PROMOTION_STATUS:
        fail("semantic promotion must remain on HOLD for source conflicts/model gaps")
    if set(raw.get("known_source_conflicts", [])) != EXPECTED_CONFLICTS:
        fail("known_source_conflicts mismatch")

    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        fail(f"rows must contain exactly {EXPECTED_ROWS} source rows")

    seen_ranges: set[tuple[float, float, str]] = set()
    all_codes: set[str] = set()
    for expected_index, row in enumerate(rows, 1):
        if row.get("source_row_index") != expected_index:
            fail(f"row index sequence breaks at {expected_index}")
        low, high, unit = row.get("frequency_min"), row.get("frequency_max"), row.get("unit")
        if not isinstance(low, (int, float)) or isinstance(low, bool):
            fail(f"row {expected_index}: invalid frequency_min")
        if not isinstance(high, (int, float)) or isinstance(high, bool) or not 0 < low < high:
            fail(f"row {expected_index}: invalid frequency range")
        if unit not in ALLOWED_UNITS:
            fail(f"row {expected_index}: invalid unit")
        key = (low, high, unit)
        if key in seen_ranges:
            fail(f"duplicate source range: {key}")
        seen_ranges.add(key)

        power = row.get("power_text")
        if not isinstance(power, str) or not power.strip():
            fail(f"row {expected_index}: power_text required")

        codes = row.get("emission_codes")
        if not isinstance(codes, list) or not codes or not all(isinstance(c, str) and c for c in codes):
            fail(f"row {expected_index}: emission_codes must be non-empty")
        if len(codes) != len(set(codes)):
            fail(f"row {expected_index}: transcription must de-duplicate repeated emission codes")
        all_codes.update(codes)

        classes = row.get("license_classes")
        if not isinstance(classes, list) or not classes or not set(classes) <= ALLOWED_CLASSES:
            fail(f"row {expected_index}: invalid license_classes")

        restrictions = row.get("restrictions")
        if not isinstance(restrictions, list) or not all(isinstance(v, str) and v.strip() for v in restrictions):
            fail(f"row {expected_index}: restrictions must be a string list")

        locator = row.get("source_locator")
        if not isinstance(locator, dict) or locator.get("document_page") not in ALLOWED_PAGES:
            fail(f"row {expected_index}: invalid source locator")
        if row.get("verification_status") != "verified_visual":
            fail(f"row {expected_index}: verification_status must be verified_visual")

    definitions = emission_map.get("definitions")
    if not isinstance(definitions, list) or len(definitions) != EXPECTED_EMISSION_DEFINITIONS:
        fail(f"expected {EXPECTED_EMISSION_DEFINITIONS} emission definitions")
    codes = [d.get("code") for d in definitions]
    if len(codes) != len(set(codes)):
        fail("duplicate emission definition code")
    if not all(isinstance(d.get("bandwidth"), str) and d["bandwidth"].strip() for d in definitions):
        fail("every emission definition needs a bandwidth")
    defined = set(codes)

    unexpected = all_codes - defined - KNOWN_UNDEFINED_EMISSIONS
    if unexpected:
        fail(f"raw table contains unexpected undefined emissions: {sorted(unexpected)}")
    missing_known = KNOWN_UNDEFINED_EMISSIONS - all_codes
    if missing_known:
        fail(f"expected source inconsistency code(s) missing from raw transcription: {sorted(missing_known)}")
    wrongly_defined = KNOWN_UNDEFINED_EMISSIONS & defined
    if wrongly_defined:
        fail(f"source-only emission code(s) must remain undefined by Tablo 26-1: {sorted(wrongly_defined)}")

    row_144 = find_row(rows, 144, 146, "MHz")
    if set(row_144["license_classes"]) != {"A", "B", "C"}:
        fail("144-146 MHz classes must be A/B/C")
    if not any("C-class" in item and "5 W" in item for item in row_144["restrictions"]):
        fail("144-146 MHz must preserve the C-class 5 W condition")

    row_50 = find_row(rows, 50, 52, "MHz")
    if set(row_50["license_classes"]) != {"A", "B"} or row_50["power_text"] != "100 W":
        fail("50-52 MHz key fields mismatch")

    row_430 = find_row(rows, 430.2, 430.7, "MHz")
    if set(row_430["license_classes"]) != {"A", "B", "C"}:
        fail("430 MHz sub-band classes must be A/B/C")

    row_1240 = find_row(rows, 1240, 1300, "MHz")
    if set(row_1240["license_classes"]) != {"A", "B"}:
        fail("1240-1300 MHz classes must be A/B")

    print(
        f"PASS: validated {len(rows)} raw BTK amateur source row(s), "
        f"{len(definitions)} emission definition(s); "
        "artifact SHA-256 is bound; semantic promotion remains HOLD for source conflicts/model gaps"
    )


def main() -> int:
    validate_payloads(load(RAW), load(EMISSIONS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
