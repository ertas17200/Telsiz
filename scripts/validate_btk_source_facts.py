#!/usr/bin/env python3
"""Validate source-preserving structured facts derived from the BTK amateur table.

This layer structures power text and already-verified raw restriction
transcriptions. It is evidence-only: it never grants or denies permission.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "data" / "btk_source_facts.json"
RAW = ROOT / "data" / "btk_amateur_table_raw.json"
SOURCES = ROOT / "data" / "sources.json"

SOURCE_ID = "TR.BTK.FTM.TECH.2022-IK-SYD-245"
EXPECTED_ROWS = 33
EXPECTED_CONFLICTS = {
    "TR-BTK-NUMBERING-001",
    "TR-BTK-EMISSION-001",
    "TR-BTK-UNIT-001",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{label}: cannot load JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{label}: root must be an object")
    return value


def expected_power_model(text: str) -> dict:
    m = re.fullmatch(r"(\d+(?:\.\d+)?) W \(e\.i\.r\.p\.\)", text)
    if m:
        return {
            "raw_text": text,
            "relationship": "SINGLE",
            "terms": [{
                "value": float(m.group(1)) if "." in m.group(1) else int(m.group(1)),
                "unit": "W",
                "basis": "eirp",
                "qualifier_text": "e.i.r.p.",
            }],
        }
    m = re.fullmatch(r"(\d+(?:\.\d+)?) W", text)
    if m:
        return {
            "raw_text": text,
            "relationship": "SINGLE",
            "terms": [{
                "value": float(m.group(1)) if "." in m.group(1) else int(m.group(1)),
                "unit": "W",
                "basis": "source_output_column",
                "qualifier_text": None,
            }],
        }
    m = re.fullmatch(r"(\d+(?:\.\d+)?) W, (\d+(?:\.\d+)?) W \(PEP\)", text)
    if m:
        conv = lambda value: float(value) if "." in value else int(value)
        return {
            "raw_text": text,
            "relationship": "SOURCE_LISTED_DUAL_VALUE_RELATION_UNRESOLVED",
            "terms": [
                {
                    "value": conv(m.group(1)),
                    "unit": "W",
                    "basis": "source_output_column",
                    "qualifier_text": None,
                },
                {
                    "value": conv(m.group(2)),
                    "unit": "W",
                    "basis": "pep",
                    "qualifier_text": "PEP",
                },
            ],
        }
    return {"raw_text": text, "relationship": "UNPARSED", "terms": []}


def expected_category(text: str) -> str:
    s = text.lower()
    if "j3e" in s or "f3e" in s or "g3e" in s:
        return "emission_subrange"
    if "training/promotion" in s:
        return "training_exception"
    if "c-class" in s:
        return "class_power_limit"
    if "handheld" in s:
        return "handheld_power_limit"
    if "beacon" in s:
        return "beacon_condition"
    if "repeater" in s:
        return "repeater_condition"
    if "earth-moon-earth" in s:
        return "eme_condition"
    if "amateur-satellite" in s:
        return "satellite_condition"
    if "emergency" in s:
        return "emergency_cooperation"
    if "primary amateur allocation" in s:
        return "allocation_note"
    if "morse code and digital" in s:
        return "mode_restriction"
    if "international amateur dx" in s:
        return "dx_note"
    return "other_source_condition"


def validate_payloads(facts: dict, raw: dict, sources_payload: dict) -> None:
    if facts.get("schema_version") != 1:
        fail("source facts schema_version must be 1")
    if facts.get("source_id") != SOURCE_ID or raw.get("source_id") != SOURCE_ID:
        fail("source facts/raw source_id mismatch")
    if facts.get("artifact_sha256") != raw.get("artifact_sha256"):
        fail("source facts artifact_sha256 must match raw artifact")
    if facts.get("model_status") != "COMPLETE_33_ROW_SOURCE_FACT_MODEL_DECISION_SEMANTICS_PARTIAL":
        fail("unexpected source facts model_status")
    if set(facts.get("global_source_conflicts", [])) != EXPECTED_CONFLICTS:
        fail("source facts conflict set mismatch")

    policy = facts.get("policy")
    required_true = (
        "evidence_only",
        "does_not_create_permission",
        "restriction_text_is_verified_transcription_not_new_legal_interpretation",
        "dual_power_relationship_remains_unresolved",
        "source_conflicts_must_not_be_normalized",
    )
    if not isinstance(policy, dict) or any(policy.get(key) is not True for key in required_true):
        fail("source facts fail-closed policy is incomplete")

    sources = {x["id"]: x for x in sources_payload.get("sources", [])}
    source = sources.get(SOURCE_ID)
    if source is None:
        fail("source facts source missing from registry")
    if source.get("verification_status") != "verified":
        fail("source facts require verified source")
    if source.get("legal_status") != "current":
        fail("source facts require current source")
    if source.get("content_sha256") != facts.get("artifact_sha256"):
        fail("source facts must bind to current source content_sha256")

    raw_rows = raw.get("rows")
    rows = facts.get("rows")
    if not isinstance(raw_rows, list) or len(raw_rows) != EXPECTED_ROWS:
        fail("raw table must contain 33 rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        fail("source facts must contain 33 rows")

    total_conditions = 0
    for raw_row, fact in zip(raw_rows, rows):
        idx = raw_row["source_row_index"]
        if fact.get("source_row_index") != idx:
            fail(f"row {idx}: source_row_index/order mismatch")

        expected_identity = {
            "frequency_min": raw_row["frequency_min"],
            "frequency_max": raw_row["frequency_max"],
            "unit": raw_row["unit"],
            "license_classes": raw_row["license_classes"],
        }
        if fact.get("raw_identity") != expected_identity:
            fail(f"row {idx}: raw_identity drift")
        if fact.get("raw_power_text") != raw_row["power_text"]:
            fail(f"row {idx}: raw_power_text drift")
        if fact.get("power_model") != expected_power_model(raw_row["power_text"]):
            fail(f"row {idx}: power_model drift")

        if fact.get("source_locator") != raw_row["source_locator"]:
            fail(f"row {idx}: source_locator drift")
        if fact.get("permission_effect") != "NONE":
            fail(f"row {idx}: source facts must not create permission effects")

        restrictions = raw_row["restrictions"]
        conditions = fact.get("conditions")
        if not isinstance(conditions, list) or len(conditions) != len(restrictions):
            fail(f"row {idx}: condition count mismatch")
        if fact.get("condition_count") != len(restrictions):
            fail(f"row {idx}: condition_count mismatch")

        for number, (raw_text, condition) in enumerate(zip(restrictions, conditions), start=1):
            if condition.get("condition_index") != number:
                fail(f"row {idx}: condition_index mismatch")
            if condition.get("transcription_text") != raw_text:
                fail(f"row {idx}: condition transcription drift")
            if condition.get("category") != expected_category(raw_text):
                fail(f"row {idx}: condition category mismatch")
            if condition.get("decision_effect") != "NOT_EVALUATED":
                fail(f"row {idx}: condition cannot claim a decision effect")
        total_conditions += len(conditions)

        serialized = json.dumps(fact, ensure_ascii=False).lower()
        for forbidden in ('"allowed":', '"not_allowed":', '"legal_status":', '"verdict":'):
            if forbidden in serialized:
                fail(f"row {idx}: forbidden decision field present: {forbidden}")

    dual_rows = sum(
        1 for row in rows
        if row["power_model"]["relationship"] == "SOURCE_LISTED_DUAL_VALUE_RELATION_UNRESOLVED"
    )
    if dual_rows != 29:
        fail(f"expected 29 dual-power rows, got {dual_rows}")
    if total_conditions != 60:
        fail(f"expected 60 source conditions, got {total_conditions}")

    print(
        f"PASS: validated {EXPECTED_ROWS} BTK source-fact row(s), "
        f"{total_conditions} condition transcription(s), {dual_rows} unresolved dual-power row(s); "
        "permission inference remains disabled"
    )


def main() -> int:
    validate_payloads(
        load(FACTS, "source facts"),
        load(RAW, "raw BTK table"),
        load(SOURCES, "source registry"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
