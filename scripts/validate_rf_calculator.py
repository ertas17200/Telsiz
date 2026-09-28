#!/usr/bin/env python3
"""Validate the source-grounded RF wavelength calculator contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "rf_calculator_contract.json"
SOURCES = ROOT / "data" / "sources.json"

EXPECTED_C = 299792458
EXPECTED_UNITS = {"Hz": 1, "kHz": 1000, "MHz": 1000000, "GHz": 1000000000}
EXPECTED_OUTPUTS = {
    "frequency_hz",
    "free_space_wavelength_m",
    "velocity_factor",
    "propagation_wavelength_m",
    "quarter_wave_m",
    "half_wave_m",
    "full_wave_m",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(path: Path, label: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{label}: cannot load JSON: {exc}")


def validate(contract: dict, source_payload: dict) -> None:
    if contract.get("schema_version") != 1:
        fail("rf calculator: schema_version must be 1")
    if contract.get("source_id") != "BIPM.SI.DEFINING_CONSTANTS":
        fail("rf calculator: unexpected source_id")
    if contract.get("speed_of_light_m_s") != EXPECTED_C:
        fail("rf calculator: exact SI speed of light must be 299792458 m/s")
    if contract.get("supported_frequency_units") != EXPECTED_UNITS:
        fail("rf calculator: frequency unit multipliers mismatch")
    if set(contract.get("outputs", [])) != EXPECTED_OUTPUTS:
        fail("rf calculator: output contract mismatch")

    vf = contract.get("velocity_factor")
    if not isinstance(vf, dict):
        fail("rf calculator: velocity_factor contract is required")
    if vf.get("minimum_exclusive") != 0 or vf.get("maximum_inclusive") != 1:
        fail("rf calculator: velocity factor range must be 0 < VF <= 1")
    if vf.get("default") != 1:
        fail("rf calculator: default velocity factor must represent free space")

    assumptions = contract.get("assumptions")
    if not isinstance(assumptions, list) or len(assumptions) < 3:
        fail("rf calculator: explicit assumptions are required")
    joined = " ".join(assumptions).lower()
    if "not guaranteed physical resonant antenna cut lengths" not in joined:
        fail("rf calculator: antenna cut-length limitation must be explicit")

    boundary = contract.get("trust_boundary")
    if not isinstance(boundary, dict):
        fail("rf calculator: trust_boundary is required")
    if boundary.get("legal_content") is not False or boundary.get("legal_verdicts") is not False:
        fail("rf calculator: legal content/verdicts must remain false")

    sources = {item["id"]: item for item in source_payload.get("sources", [])}
    source = sources.get(contract["source_id"])
    if source is None:
        fail("rf calculator: BIPM source record is missing")
    if source.get("verification_status") != "verified":
        fail("rf calculator: BIPM source must be verified")
    if source.get("source_type") != "official_technical":
        fail("rf calculator: BIPM source must be official_technical")
    if source.get("legal_status") != "not_applicable":
        fail("rf calculator: BIPM source cannot be legal authority")

    print(
        "PASS: validated RF wavelength calculator contract "
        f"(c={EXPECTED_C} m/s; {len(EXPECTED_UNITS)} frequency units)"
    )


def main() -> int:
    validate(load(CONTRACT, "RF contract"), load(SOURCES, "source registry"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
