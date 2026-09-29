#!/usr/bin/env python3
"""Validate the partial, authority-separated repeater registry."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "repeaters.json"
SOURCES = ROOT / "data" / "sources.json"

REQUIRED_RECORD_FIELDS = {
    "id",
    "region",
    "branch",
    "site",
    "band",
    "rx_mhz",
    "tx_mhz",
    "operational_status",
    "observed_at",
    "source_id",
    "source_authority_class",
    "official_permission_status",
}
ALLOWED_OPERATIONAL = {"Aktif", "Bakımda"}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(path: Path, label: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{label}: cannot load JSON: {exc}")


def valid_utc(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def validate(registry: dict, source_payload: dict) -> None:
    if registry.get("schema_version") != 1:
        fail("repeater registry: schema_version must be 1")
    if registry.get("coverage_status") != "partial_snapshot":
        fail("repeater registry: v1 coverage must remain partial_snapshot")
    if "Absence" not in registry.get("coverage_note", ""):
        fail("repeater registry: partial-coverage absence semantics must be explicit")
    if not valid_utc(registry.get("observed_at")):
        fail("repeater registry: observed_at must be UTC ISO-8601")

    policy = registry.get("freshness_policy")
    if not isinstance(policy, dict):
        fail("repeater registry: freshness_policy is required")
    days = policy.get("stale_after_days")
    if not isinstance(days, int) or isinstance(days, bool) or days <= 0:
        fail("repeater registry: stale_after_days must be a positive integer")
    if "repository" not in policy.get("policy_origin", "").lower():
        fail("repeater registry: freshness threshold must be labelled as repository policy")

    sources = {item["id"]: item for item in source_payload.get("sources", [])}
    operational_source = sources.get(registry.get("operational_source_id"))
    if operational_source is None:
        fail("repeater registry: operational source missing")
    if operational_source.get("source_type") != "amateur_association":
        fail("repeater registry: operational source must be amateur_association")
    if operational_source.get("verification_status") != "verified":
        fail("repeater registry: operational source must be verified")
    if operational_source.get("legal_status") != "not_applicable":
        fail("repeater registry: association source cannot be legal authority")

    legal_source = sources.get(registry.get("legal_authority_source_id"))
    if legal_source is None:
        fail("repeater registry: legal authority source missing")
    if legal_source.get("source_type") != "official_legal":
        fail("repeater registry: legal authority source must be official_legal")
    if legal_source.get("verification_status") != "verified":
        fail("repeater registry: legal authority source must be verified")
    if legal_source.get("legal_status") != "current":
        fail("repeater registry: legal authority source must be current")

    if "not official permission evidence" not in registry.get("permission_semantics", ""):
        fail("repeater registry: association/permission separation must be explicit")

    records = registry.get("records")
    if not isinstance(records, list) or not records:
        fail("repeater registry: records must be a non-empty list")

    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict) or set(record) != REQUIRED_RECORD_FIELDS:
            fail(f"repeaters[{index}]: exact record fields required")
        rid = record["id"]
        if not isinstance(rid, str) or not rid.startswith("TRAC."):
            fail(f"repeaters[{index}]: id must start TRAC.")
        if rid in seen:
            fail(f"duplicate repeater id: {rid}")
        seen.add(rid)

        if record["source_id"] != registry["operational_source_id"]:
            fail(f"{rid}: source_id must be the operational snapshot source")
        if record["source_authority_class"] != "amateur_association":
            fail(f"{rid}: source_authority_class must remain amateur_association")
        if record["official_permission_status"] != "UNKNOWN_NOT_VERIFIED":
            fail(f"{rid}: association data cannot promote official permission")
        if record["operational_status"] not in ALLOWED_OPERATIONAL:
            fail(f"{rid}: unsupported operational_status")
        if record["band"] not in {"VHF", "UHF"}:
            fail(f"{rid}: band must be VHF/UHF")
        if not isinstance(record["rx_mhz"], (int, float)) or isinstance(record["rx_mhz"], bool) or record["rx_mhz"] <= 0:
            fail(f"{rid}: rx_mhz must be positive")
        if not isinstance(record["tx_mhz"], (int, float)) or isinstance(record["tx_mhz"], bool) or record["tx_mhz"] <= 0:
            fail(f"{rid}: tx_mhz must be positive")
        if not valid_utc(record["observed_at"]):
            fail(f"{rid}: observed_at invalid")
        if record["observed_at"] != registry["observed_at"]:
            fail(f"{rid}: record observation must match snapshot observation")
        for key in ("region", "branch", "site"):
            if not isinstance(record[key], str) or not record[key].strip():
                fail(f"{rid}: {key} required")

    print(
        f"PASS: validated {len(records)} TRAC repeater snapshot record(s); "
        "association operational status remains separate from official permission"
    )


def main() -> int:
    validate(load(REGISTRY, "repeater registry"), load(SOURCES, "source registry"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
