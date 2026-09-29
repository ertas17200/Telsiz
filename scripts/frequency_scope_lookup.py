#!/usr/bin/env python3
"""Query BTK raw frequency/class scope without creating a legal verdict."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "data" / "frequency_scope.json"
UNIT_TO_MHZ = {"kHz": 0.001, "MHz": 1.0, "GHz": 1000.0}


def load_scope() -> dict:
    return json.loads(SCOPE_PATH.read_text(encoding="utf-8"))


def lookup_scope(scope: dict, frequency_mhz: float, license_class: str) -> dict:
    matches = []
    for entry in scope.get("entries", []):
        factor = UNIT_TO_MHZ[entry["unit"]]
        low = entry["frequency_min"] * factor
        high = entry["frequency_max"] * factor
        if low <= frequency_mhz <= high and license_class in entry["license_classes"]:
            matches.append(entry)

    return {
        "scope_status": "SOURCE_LISTED" if matches else "NOT_LISTED_IN_PRIMARY_RAW_SCOPE",
        "legal_status": "UNKNOWN",
        "permission_inference": "PROHIBITED",
        "matches": [
            {
                "id": e["id"],
                "source_row_index": e["source_row_index"],
                "frequency_min": e["frequency_min"],
                "frequency_max": e["frequency_max"],
                "unit": e["unit"],
                "license_classes": e["license_classes"],
                "observed_power_text": e["observed_power_text"],
                "source_restrictions": e["source_restrictions"],
                "conflict_ids": e["conflict_ids"],
            }
            for e in matches
        ],
        "note": (
            "Scope evidence only. SOURCE_LISTED does not mean transmission is legally allowed; "
            "the decision engine and all applicable conditions still control."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--frequency", type=float, required=True, help="MHz")
    p.add_argument("--class", dest="license_class", choices=("A", "B", "C"), required=True)
    args = p.parse_args()
    print(json.dumps(
        lookup_scope(load_scope(), args.frequency, args.license_class),
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
