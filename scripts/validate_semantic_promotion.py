#!/usr/bin/env python3
"""Validate the 33-row BTK semantic-promotion readiness map.

This gate inventories what can be promoted without inventing semantics.
It does not make the frequency table complete and does not create permission.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMOTION = ROOT / "data" / "btk_semantic_promotion.json"
RAW = ROOT / "data" / "btk_amateur_table_raw.json"
TABLE = ROOT / "data" / "frequency_table.json"
SOURCES = ROOT / "data" / "sources.json"
ARTIFACTS = ROOT / "data" / "artifacts.json"

SOURCE_ID = "TR.BTK.FTM.TECH.2022-IK-SYD-245"
EXPECTED_ROWS = 33
EXPECTED_CONFLICTS = {
    "TR-BTK-NUMBERING-001",
    "TR-BTK-EMISSION-001",
    "TR-BTK-UNIT-001",
}
UNDEFINED_EMISSIONS = {"A3J", "J2C"}
RAW_REF_RE = re.compile(r"source_row_index=(\d+)")


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


def expected_power_status(power_text: str) -> str:
    if re.fullmatch(r"\d+(?:\.\d+)? W", power_text):
        return "PROMOTABLE_OUTPUT_W"
    if re.fullmatch(r"\d+(?:\.\d+)? W \(e\.i\.r\.p\.\)", power_text):
        return "PROMOTABLE_EIRP_W"
    if "e.i.r.p." in power_text:
        return "NEEDS_POWER_BASIS_MODEL"
    if "," in power_text:
        return "NEEDS_MULTIVALUE_POWER_MODEL"
    return "NEEDS_POWER_REVIEW"


def semantic_ids_by_raw(table: dict) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {}
    rows = table.get("rows")
    if not isinstance(rows, list):
        fail("frequency table rows must be a list")
    for row in rows:
        locator = row.get("source_locator")
        if not isinstance(locator, dict):
            continue
        raw_ref = locator.get("raw_row")
        if not isinstance(raw_ref, str):
            continue
        match = RAW_REF_RE.search(raw_ref)
        if not match:
            continue
        index = int(match.group(1))
        result.setdefault(index, []).append(row["id"])
    for values in result.values():
        values.sort()
    return result


def expected_blockers(raw_row: dict) -> list[str]:
    blockers: list[str] = []
    codes = set(raw_row["emission_codes"])
    if codes & UNDEFINED_EMISSIONS:
        blockers.append("TR-BTK-EMISSION-001")
    if raw_row["source_row_index"] == 16:
        blockers.append("TR-BTK-UNIT-001")

    power = expected_power_status(raw_row["power_text"])
    if power == "NEEDS_POWER_BASIS_MODEL":
        blockers.append("SEMANTIC_POWER_BASIS_MODEL_GAP")
    elif power == "NEEDS_MULTIVALUE_POWER_MODEL":
        blockers.append("SEMANTIC_MULTIVALUE_POWER_MODEL_GAP")
    elif power == "NEEDS_POWER_REVIEW":
        blockers.append("SEMANTIC_POWER_REVIEW_REQUIRED")

    if raw_row["restrictions"]:
        blockers.append("SEMANTIC_CONDITION_MODEL_GAP")
    return blockers


def validate_payloads(
    promotion: dict,
    raw: dict,
    table: dict,
    sources_payload: dict,
    artifacts_payload: dict,
) -> None:
    if promotion.get("schema_version") != 1:
        fail("promotion map schema_version must be 1")
    if promotion.get("source_id") != SOURCE_ID or raw.get("source_id") != SOURCE_ID:
        fail("promotion/raw source_id mismatch")
    if promotion.get("source_rows_counted") != EXPECTED_ROWS:
        fail(f"promotion map must count exactly {EXPECTED_ROWS} rows")
    if promotion.get("mapping_status") != "COMPLETE_33_ROW_READINESS_MAP_SEMANTIC_PROMOTION_PARTIAL":
        fail("unexpected promotion mapping_status")
    if set(promotion.get("global_source_conflicts", [])) != EXPECTED_CONFLICTS:
        fail("promotion global_source_conflicts mismatch")

    policy = promotion.get("policy")
    if not isinstance(policy, dict) or policy.get("does_not_create_permission") is not True:
        fail("promotion policy must explicitly state does_not_create_permission=true")
    limits = policy.get("current_model_limits")
    if not isinstance(limits, list) or len(limits) < 4:
        fail("promotion policy must document current semantic-model limits")

    sources = {item["id"]: item for item in sources_payload.get("sources", [])}
    source = sources.get(SOURCE_ID)
    if source is None:
        fail("promotion source missing from source registry")
    if source.get("verification_status") != "verified":
        fail("promotion source must be verified")
    if source.get("source_type") != "official_legal" or source.get("legal_status") != "current":
        fail("promotion source must remain current official_legal")

    artifacts = {
        item["source_id"]: item for item in artifacts_payload.get("artifacts", [])
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }
    artifact = artifacts.get(SOURCE_ID)
    if artifact is None:
        fail("promotion artifact record missing")
    if artifact.get("artifact_status") != "verified_bytes":
        fail("promotion requires verified_bytes artifact status")
    if artifact.get("change_status") != "UNCHANGED" or artifact.get("reverify_required") is not False:
        fail("promotion requires an unchanged, non-reverify artifact baseline")

    digest = source.get("content_sha256")
    if not isinstance(digest, str):
        fail("promotion requires bound source content_sha256")
    if promotion.get("artifact_sha256") != digest:
        fail("promotion artifact_sha256 must match source content_sha256")
    if raw.get("artifact_sha256") != digest:
        fail("raw artifact_sha256 must match source content_sha256")
    if artifact.get("sha256") != digest:
        fail("artifact registry sha256 must match source content_sha256")

    raw_rows = raw.get("rows")
    mapped_rows = promotion.get("rows")
    if not isinstance(raw_rows, list) or len(raw_rows) != EXPECTED_ROWS:
        fail("raw table must contain 33 rows")
    if not isinstance(mapped_rows, list) or len(mapped_rows) != EXPECTED_ROWS:
        fail("promotion map must contain 33 rows")

    semantic_by_raw = semantic_ids_by_raw(table)
    seen: set[int] = set()
    for raw_row, mapped in zip(raw_rows, mapped_rows):
        index = raw_row["source_row_index"]
        if mapped.get("source_row_index") != index:
            fail(f"promotion row order/index mismatch at raw row {index}")
        if index in seen:
            fail(f"duplicate promotion source_row_index: {index}")
        seen.add(index)

        expected_identity = {
            "frequency_min": raw_row["frequency_min"],
            "frequency_max": raw_row["frequency_max"],
            "unit": raw_row["unit"],
            "license_classes": raw_row["license_classes"],
        }
        if mapped.get("raw_identity") != expected_identity:
            fail(f"row {index}: raw_identity drift")

        readiness = mapped.get("field_readiness")
        if not isinstance(readiness, dict):
            fail(f"row {index}: field_readiness is required")
        if readiness.get("frequency_range") != "PROMOTABLE_EXACT":
            fail(f"row {index}: frequency range must remain exact")
        if readiness.get("license_classes") != "PROMOTABLE_EXACT":
            fail(f"row {index}: license classes must remain exact")

        expected_power = expected_power_status(raw_row["power_text"])
        if readiness.get("power") != expected_power:
            fail(f"row {index}: power readiness mismatch")

        undefined = sorted(set(raw_row["emission_codes"]) & UNDEFINED_EMISSIONS)
        expected_emission = "BLOCKED_SOURCE_CONFLICT" if undefined else "PROMOTABLE_EXACT"
        if readiness.get("emissions") != expected_emission:
            fail(f"row {index}: emission readiness mismatch")
        if mapped.get("emission_conflict_codes") != undefined:
            fail(f"row {index}: emission conflict codes mismatch")

        expected_conditions = (
            "PROMOTABLE_EMPTY_VERIFIED"
            if not raw_row["restrictions"]
            else "NEEDS_CONDITION_MODEL"
        )
        if readiness.get("conditions") != expected_conditions:
            fail(f"row {index}: condition readiness mismatch")

        expected_ids = sorted(semantic_by_raw.get(index, []))
        if sorted(mapped.get("current_semantic_row_ids", [])) != expected_ids:
            fail(f"row {index}: current_semantic_row_ids drift")
        expected_overall = (
            "PARTIAL_PROMOTION_PRESENT" if expected_ids else "NOT_READY_CURRENT_SCHEMA"
        )
        if mapped.get("overall_status") != expected_overall:
            fail(f"row {index}: overall_status mismatch")

        blockers = mapped.get("blockers")
        if not isinstance(blockers, list) or len(blockers) != len(set(blockers)):
            fail(f"row {index}: blockers must be a unique list")
        if blockers != expected_blockers(raw_row):
            fail(f"row {index}: blockers mismatch")

    summary = promotion.get("summary")
    if not isinstance(summary, dict):
        fail("promotion summary is required")
    partial = sum(1 for row in mapped_rows if row["overall_status"] == "PARTIAL_PROMOTION_PRESENT")
    not_ready = EXPECTED_ROWS - partial
    if summary != {
        "rows_mapped": EXPECTED_ROWS,
        "rows_with_partial_semantic_promotion": partial,
        "rows_not_ready_current_schema": not_ready,
    }:
        fail("promotion summary mismatch")

    # Lock the first new conflict-safe limited promotion: raw row 17.
    row17 = next((row for row in table["rows"] if row["id"] == "TR.FTM.AMATEUR.ROW.AB.50-52"), None)
    if row17 is None:
        fail("50-52 MHz A/B limited semantic row is missing")
    if (
        row17.get("frequency_min") != 50
        or row17.get("frequency_max") != 52
        or row17.get("unit") != "MHz"
        or set(row17.get("license_class", [])) != {"A", "B"}
        or row17.get("maximum_output_power") != 100
        or row17.get("power_unit") != "W"
    ):
        fail("50-52 MHz A/B limited semantic row key fields mismatch")
    for field in (
        "emission",
        "bandwidth",
        "station_type",
        "allowed_use",
        "prohibited_use",
        "special_conditions",
        "allocation_status",
        "satellite",
        "repeater",
        "beacon",
        "emergency",
        "footnotes",
    ):
        if row17.get(field) is not None:
            fail(f"50-52 MHz limited promotion must leave {field}=null")

    print(
        f"PASS: validated semantic-promotion readiness for {EXPECTED_ROWS} raw row(s); "
        f"{partial} partial semantic row mapping(s), {not_ready} row(s) remain not ready"
    )


def main() -> int:
    validate_payloads(
        load(PROMOTION, "promotion map"),
        load(RAW, "raw BTK table"),
        load(TABLE, "frequency table"),
        load(SOURCES, "source registry"),
        load(ARTIFACTS, "artifact registry"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
