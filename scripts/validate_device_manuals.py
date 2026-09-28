#!/usr/bin/env python3
"""Validate the Yaesu FTM-400 device/manual/firmware registry."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "device_manuals.json"
SOURCES = ROOT / "data" / "sources.json"

EXPECTED_FAMILIES = {"YAESU.FTM400.DR-DE", "YAESU.FTM400.XDR-XDE"}
EXPECTED_DESTINATIONS = {"USA", "AUS", "EXP"}
EXPECTED_MODELS = {
    "YAESU.FTM400.DR-DE": {"FTM-400DR", "FTM-400DE"},
    "YAESU.FTM400.XDR-XDE": {"FTM-400XDR", "FTM-400XDE"},
}
EXPECTED_TARGETS = {
    "YAESU.FTM400.DR-DE": {"MAIN": "3.50", "DSP": "4.31"},
    "YAESU.FTM400.XDR-XDE": {"MAIN": "4.50", "DSP": "4.31"},
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(path: Path, label: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{label}: cannot load JSON: {exc}")


def validate(registry: dict, sources_payload: dict) -> None:
    if registry.get("schema_version") != 1:
        fail("device registry: schema_version must be 1")
    if registry.get("manufacturer") != "Yaesu":
        fail("device registry: manufacturer must be Yaesu")

    boundary = registry.get("trust_boundary")
    if not isinstance(boundary, dict):
        fail("device registry: trust_boundary is required")
    if boundary.get("legal_content") is not False or boundary.get("legal_verdicts") is not False:
        fail("device registry: legal content/verdicts must remain false")
    if "package-specific Firmware Upgrade Manual" not in boundary.get("instruction_policy", ""):
        fail("device registry: package-specific update-manual gate must be explicit")

    sources = {item["id"]: item for item in sources_payload.get("sources", [])}
    product = sources.get(registry.get("product_page_source_id"))
    if product is None or product.get("verification_status") != "verified":
        fail("device registry: verified Yaesu product page source is required")

    families = registry.get("model_families")
    if not isinstance(families, list) or not families:
        fail("device registry: model_families must be a non-empty list")
    by_id = {family.get("id"): family for family in families}
    if set(by_id) != EXPECTED_FAMILIES or len(by_id) != len(families):
        fail("device registry: exact two FTM-400 model families are required")

    seen_models: set[str] = set()
    for family_id, family in by_id.items():
        models = family.get("models")
        if not isinstance(models, list) or set(models) != EXPECTED_MODELS[family_id]:
            fail(f"{family_id}: exact model aliases mismatch")
        overlap = seen_models & set(models)
        if overlap:
            fail(f"{family_id}: model aliases overlap: {sorted(overlap)}")
        seen_models.update(models)

        incompatible = family.get("incompatible_family_ids")
        other = EXPECTED_FAMILIES - {family_id}
        if not isinstance(incompatible, list) or set(incompatible) != other:
            fail(f"{family_id}: incompatible family must be explicit and symmetric")

        if family.get("documented_targets") != EXPECTED_TARGETS[family_id]:
            fail(f"{family_id}: documented firmware targets mismatch")

        packages = family.get("destination_packages")
        if not isinstance(packages, dict) or set(packages) != EXPECTED_DESTINATIONS:
            fail(f"{family_id}: destination packages must be exactly USA/AUS/EXP")
        if len(set(packages.values())) != 3:
            fail(f"{family_id}: destination package filenames must be distinct")
        if family_id == "YAESU.FTM400.DR-DE" and any("XD_" in name for name in packages.values()):
            fail(f"{family_id}: XDR/XDE firmware filename leaked into DR/DE family")
        if family_id == "YAESU.FTM400.XDR-XDE" and any("400D_" in name and "400XD_" not in name for name in packages.values()):
            fail(f"{family_id}: DR/DE firmware filename leaked into XDR/XDE family")

        firmware_source = sources.get(family.get("firmware_info_source_id"))
        if firmware_source is None:
            fail(f"{family_id}: firmware source is missing")
        if firmware_source.get("source_type") != "technical_manual":
            fail(f"{family_id}: firmware source must be technical_manual")
        if firmware_source.get("verification_status") != "verified":
            fail(f"{family_id}: firmware source must be verified")
        if firmware_source.get("legal_status") != "not_applicable":
            fail(f"{family_id}: firmware source cannot be legal authority")

        manual_source = sources.get(family.get("operating_manual_source_id"))
        if manual_source is None:
            fail(f"{family_id}: operating manual source is missing")
        if manual_source.get("source_type") != "technical_manual":
            fail(f"{family_id}: operating manual source must be technical_manual")
        if manual_source.get("verification_status") != "pending":
            fail(f"{family_id}: unverified full operating manual must remain pending")
        if family.get("operating_manual_content_status") != "pending_full_content_verification":
            fail(f"{family_id}: manual content must remain fail-closed pending")

        if family.get("update_instruction_status") != "REQUIRE_PACKAGE_FIRMWARE_UPGRADE_MANUAL":
            fail(f"{family_id}: update instruction gate is missing")

    print(
        "PASS: validated Yaesu FTM-400 device registry "
        "(2 incompatible firmware families; explicit USA/AUS/EXP selection; update steps gated)"
    )


def main() -> int:
    validate(load(REGISTRY, "device registry"), load(SOURCES, "source registry"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
