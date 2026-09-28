#!/usr/bin/env python3
"""Fail-closed Yaesu FTM-400 firmware compatibility/package guard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "device_manuals.json"


def load_registry(path: Path = REGISTRY) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_model(model: str) -> str:
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model must be a non-empty string")
    return model.strip().upper()


def _families(registry: dict) -> list[dict]:
    families = registry.get("model_families")
    if not isinstance(families, list):
        raise ValueError("device registry has no model_families list")
    return families


def resolve_family(model: str, registry: dict | None = None) -> dict:
    data = registry or load_registry()
    normalized = _normalize_model(model)
    matches = [
        family
        for family in _families(data)
        if normalized in family.get("models", [])
    ]
    if len(matches) != 1:
        raise ValueError(f"unsupported or ambiguous Yaesu FTM-400 model: {normalized}")
    return matches[0]


def select_package(
    model: str,
    destination: str,
    registry: dict | None = None,
) -> dict:
    data = registry or load_registry()
    family = resolve_family(model, data)
    if not isinstance(destination, str) or not destination.strip():
        raise ValueError("destination must be one of USA, AUS or EXP")
    dest = destination.strip().upper()

    packages = family["destination_packages"]
    if dest not in packages:
        raise ValueError(
            "destination must be an explicit manufacturer destination code: USA, AUS or EXP"
        )

    return {
        "model": _normalize_model(model),
        "family_id": family["id"],
        "destination": dest,
        "main_package": packages[dest],
        "dsp_package": family["dsp_package"],
        "documented_targets": dict(family["documented_targets"]),
        "firmware_info_source_id": family["firmware_info_source_id"],
        "operating_manual_source_id": family["operating_manual_source_id"],
        "operating_manual_content_status": family["operating_manual_content_status"],
        "update_instruction_status": family["update_instruction_status"],
        "warning": (
            "Package selection is not an update procedure. Confirm the physical radio model, "
            "destination and installed versions, then read the package-specific Yaesu "
            "Firmware Upgrade Manual before writing firmware."
        ),
        "legal_verdict": None,
    }


def assess_versions(
    model: str,
    main_version: str,
    dsp_version: str,
    registry: dict | None = None,
) -> dict:
    data = registry or load_registry()
    family = resolve_family(model, data)
    if not isinstance(main_version, str) or not main_version.strip():
        raise ValueError("main_version must be a non-empty string")
    if not isinstance(dsp_version, str) or not dsp_version.strip():
        raise ValueError("dsp_version must be a non-empty string")

    targets = family["documented_targets"]
    main_matches = main_version.strip() == targets["MAIN"]
    dsp_matches = dsp_version.strip() == targets["DSP"]

    if main_matches and dsp_matches:
        status = "MATCHES_DOCUMENTED_2020_TARGETS"
    else:
        status = "DOES_NOT_MATCH_DOCUMENTED_2020_TARGETS_VERIFY_BEFORE_UPDATE"

    return {
        "model": _normalize_model(model),
        "family_id": family["id"],
        "observed": {"MAIN": main_version.strip(), "DSP": dsp_version.strip()},
        "documented_targets": dict(targets),
        "main_matches": main_matches,
        "dsp_matches": dsp_matches,
        "status": status,
        "firmware_info_source_id": family["firmware_info_source_id"],
        "update_instruction_status": family["update_instruction_status"],
        "legal_verdict": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fail-closed Yaesu FTM-400 firmware family/destination guard. "
            "Does not perform a firmware update."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    package = sub.add_parser("package", help="Select documented package by exact model/destination")
    package.add_argument("model")
    package.add_argument("destination", choices=("USA", "AUS", "EXP"))

    versions = sub.add_parser("versions", help="Compare observed versions to documented 2020 targets")
    versions.add_argument("model")
    versions.add_argument("--main", required=True)
    versions.add_argument("--dsp", required=True)

    args = parser.parse_args()
    if args.command == "package":
        result = select_package(args.model, args.destination)
    else:
        result = assess_versions(args.model, args.main, args.dsp)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
