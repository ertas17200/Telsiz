#!/usr/bin/env python3
"""Fail-closed amateur transmit evaluation over data/frequency_table.json.

``evaluate`` never answers "may I transmit here?" from the frequency alone.
It takes jurisdiction, licence class, frequency, emission, bandwidth,
requested power, station type, operating context and acknowledged special
conditions, and returns one of:

- ``ALLOWED``                  every input and row dimension resolved, no conditions
- ``ALLOWED_WITH_CONDITIONS``  as above, but the row carries conditions/footnotes
- ``NOT_ALLOWED``              every matching row explicitly blocks the request
                               (e.g. requested power above a verified limit)
- ``UNKNOWN``                  anything else — including "no row found"

A missing row is never ``NOT_ALLOWED``. Only rows whose source is a verified,
current ``official_legal`` record can contribute; IARU/TRAC material cannot
create Turkish legal permission.

Usage:
    python scripts/frequency_lookup.py --class C --frequency 145 [--power 5] [--emission F3E]
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREQUENCY_TABLE = ROOT / "data" / "frequency_table.json"
SOURCES = ROOT / "data" / "sources.json"

UNIT_TO_MHZ = {"kHz": 0.001, "MHz": 1.0, "GHz": 1000.0}
POWER_TO_W = {"mW": 0.001, "W": 1.0, "kW": 1000.0}
RESTRICTION_FIELDS = (
    "maximum_output_power",
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
)
CONTEXT_FLAGS = {"satellite", "repeater", "beacon", "emergency"}

ALLOWED = "ALLOWED"
ALLOWED_WITH_CONDITIONS = "ALLOWED_WITH_CONDITIONS"
NOT_ALLOWED = "NOT_ALLOWED"
UNKNOWN = "UNKNOWN"


@dataclass
class Request:
    jurisdiction: str | None = "TR"
    license_class: str | None = None
    frequency_mhz: float | None = None
    emission: str | None = None
    bandwidth: str | None = None
    requested_power_w: float | None = None
    station_type: str | None = None
    context: str | None = None  # simplex / repeater / satellite / beacon / emergency
    acknowledged_conditions: list[str] = field(default_factory=list)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def legal_row_sources(sources: dict[str, dict]) -> set[str]:
    return {
        source_id
        for source_id, source in sources.items()
        if source.get("source_type") == "official_legal"
        and source.get("verification_status") == "verified"
        and source.get("legal_status") == "current"
    }


def lookup(table: dict, sources: dict[str, dict], frequency_mhz: float, license_class: str) -> list[dict]:
    """Return verified official-legal rows covering the frequency for the class."""
    allowed_sources = legal_row_sources(sources)
    matches = []
    for row in table.get("rows", []):
        if row.get("verification_status") != "verified":
            continue
        if row.get("source_id") not in allowed_sources:
            continue
        factor = UNIT_TO_MHZ.get(row.get("unit"))
        if factor is None:
            continue
        low = row["frequency_min"] * factor
        high = row["frequency_max"] * factor
        if low <= frequency_mhz <= high and license_class in row["license_class"]:
            matches.append(row)
    return matches


def _row_power_w(row: dict) -> float | None:
    power = row.get("maximum_output_power")
    unit = POWER_TO_W.get(row.get("power_unit"))
    if power is None or unit is None:
        return None
    return power * unit


def _explicit_block(row: dict, request: Request, complete: bool) -> str | None:
    """Reason the row explicitly forbids the request, or None."""
    limit = _row_power_w(row)
    if request.requested_power_w is not None and limit is not None and request.requested_power_w > limit:
        return f"requested power {request.requested_power_w} W exceeds verified limit {limit} W ({row['id']})"
    prohibited = row.get("prohibited_use")
    if prohibited and request.context and request.context in prohibited:
        return f"context '{request.context}' is explicitly prohibited ({row['id']})"
    if complete:
        emissions = row.get("emission")
        if emissions is not None and request.emission and request.emission not in emissions:
            return f"emission '{request.emission}' is not listed for {row['id']}"
        if request.context in CONTEXT_FLAGS and row.get(request.context) is False:
            return f"{request.context} use is not permitted in {row['id']}"
    return None


def _full_match(row: dict, request: Request) -> list[str]:
    """Unresolved dimensions preventing a positive verdict for this row."""
    gaps = [f"row:{name}" for name in RESTRICTION_FIELDS if row.get(name) is None]
    for name in ("emission", "bandwidth", "requested_power_w", "station_type", "context"):
        if getattr(request, name) in (None, ""):
            gaps.append(f"input:{name}")
    if gaps:
        return gaps
    if request.emission not in row["emission"]:
        gaps.append("emission_not_listed")
    if request.bandwidth != row["bandwidth"]:
        gaps.append("bandwidth_not_confirmed")
    if request.station_type not in row["station_type"]:
        gaps.append("station_type_not_listed")
    if request.context in CONTEXT_FLAGS and row[request.context] is not True:
        gaps.append(f"{request.context}_not_confirmed")
    if request.context not in CONTEXT_FLAGS and request.context not in row["allowed_use"]:
        gaps.append("context_not_listed")
    return gaps


def evaluate(table: dict, sources: dict[str, dict], request: Request) -> dict:
    complete = table.get("coverage_status") == "complete"
    result = {
        "legal_status": UNKNOWN,
        "reasons": [],
        "rows": [],
        "known_limits": [],
        "conditions": [],
        "missing": [],
        "coverage_status": table.get("coverage_status"),
    }

    if request.jurisdiction != "TR":
        result["reasons"].append("jurisdiction not covered by the Turkish legal table")
        return result
    missing_inputs = [
        name for name in ("license_class", "frequency_mhz") if getattr(request, name) in (None, "")
    ]
    if missing_inputs:
        result["missing"] = [f"input:{name}" for name in missing_inputs]
        result["reasons"].append("licence class and frequency are required")
        return result

    rows = lookup(table, sources, request.frequency_mhz, request.license_class)
    result["rows"] = [row["id"] for row in rows]
    result["known_limits"] = [
        {"row": row["id"], "max_output_power": row["maximum_output_power"], "power_unit": row["power_unit"]}
        for row in rows
        if row.get("maximum_output_power") is not None
    ]
    if not rows:
        result["reasons"].append(
            "no verified official row covers this frequency/class; absence is not a prohibition"
        )
        return result

    blocks = [_explicit_block(row, request, complete) for row in rows]
    if all(blocks):
        result["legal_status"] = NOT_ALLOWED
        result["reasons"] = blocks
        return result

    if not complete:
        result["reasons"].append("frequency table coverage is partial; no blanket legal verdict")
    candidates = [row for row, block in zip(rows, blocks) if block is None]
    gaps = {row["id"]: _full_match(row, request) for row in candidates}
    result["missing"] = sorted({gap for row_gaps in gaps.values() for gap in row_gaps})
    resolved = [row for row in candidates if not gaps[row["id"]]]
    if not complete or len(resolved) != len(rows):
        if result["missing"]:
            result["reasons"].append("unresolved dimensions; permission is not inferred")
        return result

    conditions = sorted(
        {c for row in resolved for c in row["special_conditions"] + row["footnotes"]}
    )
    result["conditions"] = conditions
    result["unacknowledged_conditions"] = [
        c for c in conditions if c not in request.acknowledged_conditions
    ]
    result["legal_status"] = ALLOWED_WITH_CONDITIONS if conditions else ALLOWED
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--class", dest="license_class")
    parser.add_argument("--frequency", type=float, dest="frequency_mhz", help="MHz")
    parser.add_argument("--power", type=float, dest="requested_power_w", help="W")
    parser.add_argument("--emission")
    parser.add_argument("--bandwidth")
    parser.add_argument("--station-type", dest="station_type")
    parser.add_argument("--context")
    parser.add_argument("--jurisdiction", default="TR")
    args = parser.parse_args()
    sources = {s["id"]: s for s in load_json(SOURCES)["sources"]}
    request = Request(**vars(args))
    print(json.dumps(evaluate(load_json(FREQUENCY_TABLE), sources, request), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
