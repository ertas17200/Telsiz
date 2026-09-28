#!/usr/bin/env python3
"""Validate source-grounded Q-code and RS(T) training data."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Q_CODES = ROOT / "data" / "q_codes.json"
RST = ROOT / "data" / "rst_reports.json"
SOURCES = ROOT / "data" / "sources.json"

EXPECTED_Q_CODES = {
    "QRG", "QRK", "QRL", "QRM", "QRN", "QRO", "QRP", "QRS", "QRT", "QRU",
    "QRV", "QRX", "QRZ", "QSB", "QSL", "QSO", "QSX", "QSY", "QTH", "QUF",
}
EXPECTED_Q_SOURCES = {"IARU.R1.EOP.4.2.0", "ITU.R.M1172.0"}
EXPECTED_RST_SOURCES = {"IARU.R1.EOP.4.2.0", "IARU.R1.VHF.HANDBOOK.10.02"}
Q_RE = re.compile(r"^Q[A-Z]{2}$")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(path: Path, label: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{label}: cannot load JSON: {exc}")


def _verified_nonlegal_sources(
    source_ids: list[str],
    sources: dict[str, dict],
    label: str,
) -> None:
    for source_id in source_ids:
        source = sources.get(source_id)
        if source is None:
            fail(f"{label}: missing source {source_id}")
        if source.get("verification_status") != "verified":
            fail(f"{label}: source {source_id} must be verified")
        if source.get("legal_status") != "not_applicable":
            fail(f"{label}: source {source_id} must not be treated as Turkish legal authority")


def validate(q_payload: dict, rst_payload: dict, sources_payload: dict) -> None:
    if q_payload.get("schema_version") != 1 or rst_payload.get("schema_version") != 1:
        fail("operator codes: schema_version must be 1")

    sources = {s["id"]: s for s in sources_payload.get("sources", [])}
    q_source_ids = q_payload.get("source_ids")
    rst_source_ids = rst_payload.get("source_ids")

    if not isinstance(q_source_ids, list) or set(q_source_ids) != EXPECTED_Q_SOURCES:
        fail("Q-code source_ids do not match the grounded contract")
    if not isinstance(rst_source_ids, list) or set(rst_source_ids) != EXPECTED_RST_SOURCES:
        fail("RST source_ids do not match the grounded contract")

    _verified_nonlegal_sources(q_source_ids, sources, "Q-code")
    _verified_nonlegal_sources(rst_source_ids, sources, "RST")

    codes = q_payload.get("codes")
    if not isinstance(codes, list):
        fail("Q-code codes must be a list")

    seen: set[str] = set()
    for item in codes:
        if not isinstance(item, dict):
            fail("Q-code entry must be an object")
        if set(item) != {"code", "question_summary", "statement_summary", "topic"}:
            fail("Q-code entry has missing or unknown fields")

        code = item["code"]
        if not isinstance(code, str) or not Q_RE.fullmatch(code):
            fail(f"invalid Q-code: {code!r}")
        if code in seen:
            fail(f"duplicate Q-code: {code}")
        seen.add(code)

        for key in ("question_summary", "statement_summary", "topic"):
            if not isinstance(item[key], str) or len(item[key].strip()) < 3:
                fail(f"{code}: {key} is required")

    if seen != EXPECTED_Q_CODES:
        fail(
            f"Q-code subset mismatch missing={sorted(EXPECTED_Q_CODES - seen)} "
            f"extra={sorted(seen - EXPECTED_Q_CODES)}"
        )

    expected_ranges = {
        "readability": {str(i) for i in range(1, 6)},
        "strength": {str(i) for i in range(1, 10)},
        "tone": {str(i) for i in range(1, 10)},
    }
    for key, expected in expected_ranges.items():
        mapping = rst_payload.get(key)
        if not isinstance(mapping, dict) or set(mapping) != expected:
            fail(f"RST {key} scale has the wrong numeric range")
        if not all(isinstance(v, str) and len(v.strip()) >= 3 for v in mapping.values()):
            fail(f"RST {key} descriptions must be non-empty strings")

    count = (
        len(rst_payload["readability"])
        + len(rst_payload["strength"])
        + len(rst_payload["tone"])
    )
    print(
        f"PASS: validated {len(codes)} Q-code training entries and "
        f"{count} RS(T) scale entries"
    )


def main() -> int:
    validate(
        load(Q_CODES, "Q-code data"),
        load(RST, "RST data"),
        load(SOURCES, "source registry"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
