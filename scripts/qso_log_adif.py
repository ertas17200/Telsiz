#!/usr/bin/env python3
"""Bounded ADIF 3.1.7 ADI exporter for Telsiz QSO records."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "qso_log_contract.json"
TIME_RE = re.compile(r"^(\d{4}|\d{6})$")


def load_contract(path: Path = CONTRACT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _printable_ascii(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    if not value.isascii() or any(ord(ch) < 32 or ord(ch) > 126 for ch in value):
        raise ValueError(f"{field} must contain printable ASCII only")
    return value


def _validate_date(value: str) -> None:
    if len(value) != 8 or not value.isdigit():
        raise ValueError("QSO_DATE must use YYYYMMDD")
    try:
        parsed = datetime.strptime(value, "%Y%m%d")
    except ValueError as exc:
        raise ValueError("QSO_DATE must be a valid calendar date") from exc
    if parsed.strftime("%Y%m%d") != value:
        raise ValueError("QSO_DATE must use canonical YYYYMMDD")


def _validate_time(value: str) -> None:
    if not TIME_RE.fullmatch(value):
        raise ValueError("TIME_ON must use HHMM or HHMMSS")
    hour = int(value[0:2])
    minute = int(value[2:4])
    second = int(value[4:6]) if len(value) == 6 else 0
    if hour > 23 or minute > 59 or second > 59:
        raise ValueError("TIME_ON contains an invalid UTC time")


def _validate_freq(value: str) -> None:
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("FREQ must be a positive decimal MHz value") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("FREQ must be a positive decimal MHz value")


def validate_record(record: dict, contract: dict | None = None) -> dict:
    if not isinstance(record, dict):
        raise ValueError("QSO record must be an object")
    rules = contract or load_contract()

    supported = set(rules["required_fields"]) | set(rules["at_least_one_of"]) | set(
        rules["optional_fields"]
    )
    unknown = set(record) - supported
    if unknown:
        raise ValueError(f"unsupported QSO fields: {sorted(unknown)}")

    missing = [name for name in rules["required_fields"] if name not in record]
    if missing:
        raise ValueError(f"missing required QSO fields: {missing}")
    if not any(name in record for name in rules["at_least_one_of"]):
        raise ValueError(
            f"at least one of {rules['at_least_one_of']} must be present"
        )

    normalized: dict[str, str] = {}
    for field, raw in record.items():
        normalized[field] = _printable_ascii(raw, field)

    _validate_date(normalized["QSO_DATE"])
    _validate_time(normalized["TIME_ON"])
    if "FREQ" in normalized:
        _validate_freq(normalized["FREQ"])

    return normalized


def adi_data_specifier(field: str, value: str) -> str:
    return f"<{field}:{len(value)}>{value}"


def export_record(record: dict, contract: dict | None = None) -> str:
    rules = contract or load_contract()
    valid = validate_record(record, rules)
    parts = [
        adi_data_specifier(field, valid[field])
        for field in rules["field_order"]
        if field in valid
    ]
    return "".join(parts) + "<EOR>"


def export_log(
    records: list[dict],
    program_id: str = "TELSIZ",
    contract: dict | None = None,
) -> str:
    if not isinstance(records, list) or not records:
        raise ValueError("records must be a non-empty list")
    rules = contract or load_contract()
    program = _printable_ascii(program_id, "PROGRAMID")

    version = rules["adif_version"]
    header = (
        adi_data_specifier("ADIF_VER", version)
        + adi_data_specifier("PROGRAMID", program)
        + "<EOH>"
    )
    body = "\n".join(export_record(record, rules) for record in records)
    return header + "\n" + body + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a bounded Telsiz QSO JSON list to ADIF 3.1.7 ADI."
    )
    parser.add_argument("input", type=Path, help="JSON file containing a list of QSO objects")
    parser.add_argument("--output", type=Path, help="Write ADI output to this file")
    parser.add_argument("--program-id", default="TELSIZ")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    output = export_log(payload, args.program_id)
    if args.output:
        args.output.write_text(output, encoding="ascii", newline="\n")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
