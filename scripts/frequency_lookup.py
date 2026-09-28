#!/usr/bin/env python3
"""Fail-closed frequency/licence-class lookup over data/frequency_table.json.

A matching frequency row never means "legal to transmit" on its own. The
lookup only returns ``legal_to_transmit=True`` when the table coverage is
``complete`` and every restriction dimension of the matching row has been
extracted. Otherwise the answer stays ``UNDETERMINED`` or ``UNKNOWN``.

Usage:
    python scripts/frequency_lookup.py 145 C
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREQUENCY_TABLE = ROOT / "data" / "frequency_table.json"

UNIT_TO_MHZ = {"kHz": 0.001, "MHz": 1.0, "GHz": 1000.0}
RESTRICTION_FIELDS = (
    "maximum_output_power",
    "emission",
    "bandwidth",
    "station_type",
    "allowed_use",
    "prohibited_use",
    "special_condition",
    "secondary_allocation",
    "satellite",
    "repeater",
    "beacon",
    "emergency",
    "footnote",
)


def load_table(path: Path = FREQUENCY_TABLE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def lookup(table: dict, frequency_mhz: float, license_class: str) -> dict:
    complete = table.get("coverage_status") == "complete"
    matches = []
    for row in table.get("rows", []):
        if row.get("verification_status") != "verified":
            continue
        factor = UNIT_TO_MHZ.get(row.get("unit"))
        if factor is None:
            continue
        low = row["frequency_min"] * factor
        high = row["frequency_max"] * factor
        if low <= frequency_mhz <= high and license_class in row["license_class"]:
            matches.append(row)

    if not matches:
        return {
            "status": "NOT_IN_TABLE" if complete else "UNKNOWN_NOT_EXTRACTED",
            "legal_to_transmit": False if complete else None,
            "rows": [],
            "coverage_status": table.get("coverage_status"),
            "missing_dimensions": [],
        }

    missing = sorted(
        {field for row in matches for field in RESTRICTION_FIELDS if row.get(field) is None}
    )
    resolved = complete and not missing
    return {
        "status": "RESOLVED" if resolved else "PARTIAL_MATCH_UNDETERMINED",
        "legal_to_transmit": True if resolved else None,
        "rows": [row["id"] for row in matches],
        "maximum_output_power": [
            (row["maximum_output_power"], row["power_unit"]) for row in matches
        ],
        "source_locators": [(row["source_id"], row["source_locator"]) for row in matches],
        "coverage_status": table.get("coverage_status"),
        "missing_dimensions": missing,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2
    result = lookup(load_table(), float(argv[1]), argv[2].upper())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
