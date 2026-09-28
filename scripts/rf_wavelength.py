#!/usr/bin/env python3
"""Source-grounded RF wavelength and electrical-length calculator."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "rf_calculator_contract.json"


def load_contract(path: Path = CONTRACT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _decimal(value: object, label: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite positive number")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be a finite positive number") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError(f"{label} must be a finite positive number")
    return number


def calculate(
    frequency: object,
    unit: str = "MHz",
    velocity_factor: object = 1,
    contract: dict | None = None,
) -> dict:
    rules = contract or load_contract()
    units = rules["supported_frequency_units"]
    if unit not in units:
        raise ValueError(f"unsupported frequency unit: {unit}")

    freq = _decimal(frequency, "frequency")
    vf = _decimal(velocity_factor, "velocity_factor")
    if vf > Decimal(str(rules["velocity_factor"]["maximum_inclusive"])):
        raise ValueError("velocity_factor must be greater than 0 and at most 1")

    with localcontext() as ctx:
        ctx.prec = 34
        freq_hz = freq * Decimal(str(units[unit]))
        c = Decimal(str(rules["speed_of_light_m_s"]))
        free_space = c / freq_hz
        propagation = free_space * vf
        quarter = propagation / Decimal(4)
        half = propagation / Decimal(2)

    return {
        "frequency_hz": float(freq_hz),
        "free_space_wavelength_m": float(free_space),
        "velocity_factor": float(vf),
        "propagation_wavelength_m": float(propagation),
        "quarter_wave_m": float(quarter),
        "half_wave_m": float(half),
        "full_wave_m": float(propagation),
        "source_id": rules["source_id"],
        "assumptions": list(rules["assumptions"]),
        "legal_verdict": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Calculate ideal RF wavelength/electrical lengths from the exact SI "
            "speed of light. This is not an antenna cut-length or transmit-permission tool."
        )
    )
    parser.add_argument("frequency", help="Positive frequency value")
    parser.add_argument(
        "--unit",
        choices=("Hz", "kHz", "MHz", "GHz"),
        default="MHz",
    )
    parser.add_argument(
        "--velocity-factor",
        default="1",
        help="Propagation velocity ratio 0 < VF <= 1; default 1 (free space)",
    )
    args = parser.parse_args()

    result = calculate(args.frequency, args.unit, args.velocity_factor)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
