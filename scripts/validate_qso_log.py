#!/usr/bin/env python3
"""Validate the Telsiz bounded QSO log / ADIF export contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "qso_log_contract.json"
SOURCES = ROOT / "data" / "sources.json"

EXPECTED_REQUIRED = {"CALL", "QSO_DATE", "TIME_ON", "MODE"}
EXPECTED_ANY = {"BAND", "FREQ"}
EXPECTED_OPTIONAL = {"RST_SENT", "RST_RCVD", "GRIDSQUARE", "COMMENT"}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(path: Path, label: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{label}: cannot load JSON: {exc}")


def validate(contract: dict, sources_payload: dict) -> None:
    if contract.get("schema_version") != 1:
        fail("qso log: schema_version must be 1")
    if contract.get("source_id") != "ADIF.SPEC.3.1.7":
        fail("qso log: source_id must be ADIF.SPEC.3.1.7")
    if contract.get("adif_version") != "3.1.7":
        fail("qso log: exporter version must be 3.1.7")
    if contract.get("export_format") != "ADI":
        fail("qso log: v1 export_format must be ADI")

    sources = {item["id"]: item for item in sources_payload.get("sources", [])}
    source = sources.get(contract["source_id"])
    if source is None:
        fail("qso log: ADIF source record is missing")
    if source.get("verification_status") != "verified":
        fail("qso log: ADIF source must be verified")
    if source.get("source_type") != "technical_manual":
        fail("qso log: ADIF source must be technical_manual")
    if source.get("legal_status") != "not_applicable":
        fail("qso log: ADIF source cannot be treated as legal permission")

    if set(contract.get("required_fields", [])) != EXPECTED_REQUIRED:
        fail("qso log: required_fields mismatch")
    if set(contract.get("at_least_one_of", [])) != EXPECTED_ANY:
        fail("qso log: at_least_one_of mismatch")
    if set(contract.get("optional_fields", [])) != EXPECTED_OPTIONAL:
        fail("qso log: optional_fields mismatch")

    order = contract.get("field_order")
    expected_all = EXPECTED_REQUIRED | EXPECTED_ANY | EXPECTED_OPTIONAL
    if (
        not isinstance(order, list)
        or len(order) != len(set(order))
        or set(order) != expected_all
    ):
        fail("qso log: field_order must contain every supported field exactly once")

    boundary = contract.get("trust_boundary")
    if not isinstance(boundary, dict):
        fail("qso log: trust_boundary is required")
    if boundary.get("legal_content") is not False:
        fail("qso log: legal_content must remain false")
    if boundary.get("legal_verdicts") is not False:
        fail("qso log: legal_verdicts must remain false")

    print(
        "PASS: validated bounded QSO log contract for ADIF 3.1.7 "
        f"({len(expected_all)} supported fields)"
    )


def main() -> int:
    validate(load(CONTRACT, "qso log contract"), load(SOURCES, "source registry"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
