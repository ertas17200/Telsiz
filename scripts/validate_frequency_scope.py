#!/usr/bin/env python3
"""Validate the fail-closed 1:1 BTK frequency/class scope index."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "btk_amateur_table_raw.json"
SCOPE_PATH = ROOT / "data" / "frequency_scope.json"
CONFLICTS_PATH = ROOT / "docs" / "SOURCE_CONFLICTS.md"

UNITS = {"kHz", "MHz", "GHz"}
CLASSES = {"A", "B", "C"}
ID_RE = re.compile(r"^TR\.FTM\.AMATEUR\.SCOPE\.R\d{2}$")
CONFLICT_RE = re.compile(r"^##\s+(TR-BTK-[A-Z]+-\d+)\s*$", re.MULTILINE)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot load {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path}: root must be object")
    return value


def main() -> int:
    raw = load(RAW_PATH)
    scope = load(SCOPE_PATH)

    if scope.get("schema_version") != 1:
        fail("schema_version must be 1")
    if scope.get("source_id") != raw.get("source_id"):
        fail("scope source_id must match raw source_id")
    if scope.get("coverage_status") != "complete_raw_scope_index":
        fail("coverage_status must be complete_raw_scope_index")
    semantics = scope.get("scope_semantics")
    if not isinstance(semantics, str) or "never means transmission is legally allowed" not in semantics:
        fail("scope_semantics must explicitly disclaim legal permission")

    raw_rows = raw.get("rows")
    entries = scope.get("entries")
    if not isinstance(raw_rows, list) or len(raw_rows) != 33:
        fail("raw table must contain exactly 33 rows")
    if not isinstance(entries, list) or len(entries) != len(raw_rows):
        fail("scope index must contain exactly one entry per raw row")

    known_conflicts = set(CONFLICT_RE.findall(CONFLICTS_PATH.read_text(encoding="utf-8")))
    globals_ = scope.get("global_conflicts")
    if not isinstance(globals_, list) or not set(globals_) <= known_conflicts:
        fail("global_conflicts contains unknown IDs")

    seen_ids: set[str] = set()
    seen_rows: set[int] = set()
    raw_by_index = {row["source_row_index"]: row for row in raw_rows}

    for entry in entries:
        if not isinstance(entry, dict):
            fail("scope entry must be object")
        required = {
            "id", "source_row_index", "frequency_min", "frequency_max", "unit",
            "license_classes", "observed_power_text", "source_restrictions",
            "source_locator", "conflict_ids", "verification_status", "decision_authority",
        }
        missing = required - set(entry)
        if missing:
            fail(f"scope entry missing fields: {sorted(missing)}")

        entry_id = entry["id"]
        if not isinstance(entry_id, str) or not ID_RE.fullmatch(entry_id):
            fail(f"invalid scope id: {entry_id!r}")
        if entry_id in seen_ids:
            fail(f"duplicate scope id: {entry_id}")
        seen_ids.add(entry_id)

        idx = entry["source_row_index"]
        if not isinstance(idx, int) or isinstance(idx, bool) or idx not in raw_by_index:
            fail(f"{entry_id}: invalid source_row_index")
        if idx in seen_rows:
            fail(f"duplicate source_row_index: {idx}")
        seen_rows.add(idx)
        if entry_id != f"TR.FTM.AMATEUR.SCOPE.R{idx:02d}":
            fail(f"{entry_id}: id does not match source_row_index")

        raw_row = raw_by_index[idx]
        for field in ("frequency_min", "frequency_max", "unit", "license_classes", "observed_power_text", "source_restrictions", "source_locator"):
            raw_field = "power_text" if field == "observed_power_text" else (
                "restrictions" if field == "source_restrictions" else field
            )
            if entry[field] != raw_row[raw_field]:
                fail(f"{entry_id}: {field} diverges from raw row")

        if entry["unit"] not in UNITS:
            fail(f"{entry_id}: invalid unit")
        classes = entry["license_classes"]
        if not isinstance(classes, list) or not classes or not set(classes) <= CLASSES:
            fail(f"{entry_id}: invalid license_classes")
        if entry["verification_status"] != "verified_visual":
            fail(f"{entry_id}: verification_status must preserve raw visual state")
        if entry["decision_authority"] != "scope_evidence_only":
            fail(f"{entry_id}: decision_authority must be scope_evidence_only")

        conflicts = entry["conflict_ids"]
        if not isinstance(conflicts, list) or not set(conflicts) <= known_conflicts:
            fail(f"{entry_id}: conflict_ids contains unknown IDs")

        has_emission_conflict = (
            "A3J" in raw_row.get("emission_codes", [])
            or "J2C" in raw_row.get("emission_codes", [])
        )
        if has_emission_conflict != ("TR-BTK-EMISSION-001" in conflicts):
            fail(f"{entry_id}: emission-conflict mapping is inconsistent")
        if (idx == 16) != ("TR-BTK-UNIT-001" in conflicts):
            fail(f"{entry_id}: unit-conflict mapping is inconsistent")

        # Conditional B-class exceptions in restriction prose must not be
        # promoted into the row's primary class envelope.
        if idx in {8, 16} and "B" in classes:
            fail(f"{entry_id}: conditional B-class use must not be promoted into primary scope")

    expected_rows = set(range(1, 34))
    if seen_rows != expected_rows:
        fail(f"scope rows mismatch: missing={sorted(expected_rows-seen_rows)} extra={sorted(seen_rows-expected_rows)}")

    print(
        f"PASS: validated {len(entries)} BTK frequency scope entries; "
        "scope is evidence-only and cannot create a legal transmit verdict"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
