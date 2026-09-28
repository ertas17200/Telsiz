#!/usr/bin/env python3
"""Fail-closed validator for Telsiz source and rule registries.

Uses only the Python standard library so validation can run in a clean
GitHub Actions runner without installing dependencies.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources.json"
RULES = ROOT / "data" / "rules.json"
FREQUENCY_TABLE = ROOT / "data" / "frequency_table.json"

ALLOWED_TYPES = {
    "official_legal",
    "official_technical",
    "amateur_association",
    "technical_manual",
    "educational",
    "community",
}
ALLOWED_VERIFICATION = {"verified", "pending", "unverified", "deprecated"}
ALLOWED_LEGAL_STATUS = {
    "current",
    "superseded",
    "repealed",
    "unknown",
    "not_applicable",
}
ALLOWED_RULE_TYPES = {
    "permission",
    "prohibition",
    "obligation",
    "condition",
    "definition",
    "limit",
    "guidance",
}
ALLOWED_AUTHORITIES = {"legal", "official_technical", "amateur_practice"}
ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{2,95}$")
SHA_RE = re.compile(r"^(sha256:)?[a-fA-F0-9]{64}$")
ALLOWED_COVERAGE = {"partial", "complete"}
ALLOWED_FREQ_UNITS = {"kHz", "MHz", "GHz"}
ALLOWED_LICENSE_CLASSES = {"A", "B", "C"}
FREQUENCY_ROW_FIELDS = {
    "id",
    "frequency_min",
    "frequency_max",
    "unit",
    "license_class",
    "maximum_output_power",
    "power_unit",
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
    "source_id",
    "source_locator",
    "verification_status",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def valid_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def load_json(path: Path, label: str) -> dict:
    if not path.exists():
        fail(f"missing {label}: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {label}: {exc}")
    if not isinstance(payload, dict):
        fail(f"{label} root must be an object")
    if payload.get("schema_version") != 1:
        fail(f"{label} schema_version must be 1")
    return payload


def validate_source(source: dict, index: int, seen_ids: set[str]) -> None:
    required = {
        "id",
        "title",
        "publisher",
        "source_type",
        "jurisdiction",
        "url",
        "topics",
        "verification_status",
        "verified_at",
    }
    missing = sorted(required - source.keys())
    if missing:
        fail(f"sources[{index}] missing required fields: {', '.join(missing)}")

    source_id = source["id"]
    if not isinstance(source_id, str) or not ID_RE.fullmatch(source_id):
        fail(f"sources[{index}].id is invalid: {source_id!r}")
    if source_id in seen_ids:
        fail(f"duplicate source id: {source_id}")
    seen_ids.add(source_id)

    if source["source_type"] not in ALLOWED_TYPES:
        fail(f"{source_id}: invalid source_type")

    if source["verification_status"] not in ALLOWED_VERIFICATION:
        fail(f"{source_id}: invalid verification_status")

    url = source["url"]
    if not isinstance(url, str):
        fail(f"{source_id}: url must be a string")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{source_id}: url must be absolute HTTPS")

    topics = source["topics"]
    if not isinstance(topics, list) or not topics or not all(
        isinstance(t, str) and len(t.strip()) >= 2 for t in topics
    ):
        fail(f"{source_id}: topics must be a non-empty string list")

    verified_at = source["verified_at"]
    if source["verification_status"] == "verified":
        if not isinstance(verified_at, str) or not valid_iso_datetime(verified_at):
            fail(f"{source_id}: verified source requires valid verified_at")
    elif verified_at is not None and (
        not isinstance(verified_at, str) or not valid_iso_datetime(verified_at)
    ):
        fail(f"{source_id}: invalid verified_at")

    legal_status = source.get("legal_status")
    if legal_status is not None and legal_status not in ALLOWED_LEGAL_STATUS:
        fail(f"{source_id}: invalid legal_status")

    digest = source.get("content_sha256")
    if digest is not None and (
        not isinstance(digest, str) or not SHA_RE.fullmatch(digest)
    ):
        fail(f"{source_id}: invalid content_sha256")

    if source["source_type"] == "official_legal":
        if not legal_status:
            fail(f"{source_id}: official_legal requires legal_status")
        if source["verification_status"] == "verified" and legal_status == "unknown":
            fail(f"{source_id}: verified current-use legal source cannot have unknown status")


def validate_rule(
    rule: dict,
    index: int,
    seen_ids: set[str],
    sources_by_id: dict[str, dict],
) -> None:
    required = {
        "id",
        "jurisdiction",
        "topic",
        "rule_type",
        "authority",
        "claim",
        "source_id",
        "source_locator",
        "verification_status",
        "verified_at",
        "conditions",
        "answer_tags",
    }
    missing = sorted(required - rule.keys())
    if missing:
        fail(f"rules[{index}] missing required fields: {', '.join(missing)}")

    rule_id = rule["id"]
    if not isinstance(rule_id, str) or not ID_RE.fullmatch(rule_id):
        fail(f"rules[{index}].id is invalid: {rule_id!r}")
    if rule_id in seen_ids:
        fail(f"duplicate rule id: {rule_id}")
    seen_ids.add(rule_id)

    if rule["rule_type"] not in ALLOWED_RULE_TYPES:
        fail(f"{rule_id}: invalid rule_type")
    if rule["authority"] not in ALLOWED_AUTHORITIES:
        fail(f"{rule_id}: invalid authority")
    if rule["verification_status"] not in ALLOWED_VERIFICATION:
        fail(f"{rule_id}: invalid verification_status")

    if not isinstance(rule["claim"], str) or len(rule["claim"].strip()) < 8:
        fail(f"{rule_id}: claim is too short")

    conditions = rule["conditions"]
    if not isinstance(conditions, list) or not all(
        isinstance(v, str) and len(v.strip()) >= 2 for v in conditions
    ):
        fail(f"{rule_id}: conditions must be a string list")

    tags = rule["answer_tags"]
    if not isinstance(tags, list) or not tags or not all(
        isinstance(v, str) and len(v.strip()) >= 2 for v in tags
    ):
        fail(f"{rule_id}: answer_tags must be a non-empty string list")

    locator = rule["source_locator"]
    if not isinstance(locator, dict) or not locator:
        fail(f"{rule_id}: source_locator must be a non-empty object")
    if not any(isinstance(v, str) and v.strip() for v in locator.values()):
        fail(f"{rule_id}: source_locator must contain at least one usable locator")

    verified_at = rule["verified_at"]
    if rule["verification_status"] == "verified":
        if not isinstance(verified_at, str) or not valid_iso_datetime(verified_at):
            fail(f"{rule_id}: verified rule requires valid verified_at")
    elif verified_at is not None and (
        not isinstance(verified_at, str) or not valid_iso_datetime(verified_at)
    ):
        fail(f"{rule_id}: invalid verified_at")

    source_id = rule["source_id"]
    source = sources_by_id.get(source_id)
    if source is None:
        fail(f"{rule_id}: unknown source_id {source_id}")

    if rule["verification_status"] == "verified":
        if source["verification_status"] != "verified":
            fail(f"{rule_id}: verified rule cannot cite non-verified source {source_id}")

    authority = rule["authority"]
    source_type = source["source_type"]
    if authority == "legal" and source_type != "official_legal":
        fail(f"{rule_id}: legal rule must cite official_legal source")
    if authority == "official_technical" and source_type not in {
        "official_legal",
        "official_technical",
    }:
        fail(f"{rule_id}: official_technical rule must cite an official source")
    if authority == "amateur_practice" and source_type not in {
        "amateur_association",
        "technical_manual",
        "educational",
    }:
        fail(f"{rule_id}: amateur_practice rule cites unsuitable source type")

    if (
        rule["verification_status"] == "verified"
        and authority == "legal"
        and source.get("legal_status") != "current"
    ):
        fail(f"{rule_id}: verified legal rule requires a current legal source")

    parameters = rule.get("parameters")
    if parameters is not None and not isinstance(parameters, dict):
        fail(f"{rule_id}: parameters must be an object")


def validate_frequency_table(
    table: dict,
    sources_by_id: dict[str, dict],
    rules_by_id: dict[str, dict],
) -> None:
    coverage = table.get("coverage_status")
    if coverage not in ALLOWED_COVERAGE:
        fail("frequency table: invalid coverage_status")

    table_source = sources_by_id.get(table.get("source_id"))
    if table_source is None:
        fail("frequency table: unknown source_id")

    if coverage == "partial":
        blocker = table.get("coverage_blocker")
        if not isinstance(blocker, str) or len(blocker.strip()) < 8:
            fail("frequency table: partial coverage requires a coverage_blocker")
    else:
        if table.get("coverage_blocker") is not None:
            fail("frequency table: complete coverage cannot carry a blocker")
        if table_source["verification_status"] != "verified":
            fail("frequency table: complete coverage requires a verified source")
        if not table_source.get("content_sha256"):
            fail("frequency table: complete coverage requires source content_sha256")

    rows = table.get("rows")
    if not isinstance(rows, list):
        fail("frequency table: rows must be a list")

    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            fail(f"frequency rows[{index}] must be an object")
        missing = sorted(FREQUENCY_ROW_FIELDS - row.keys())
        if missing:
            fail(f"frequency rows[{index}] missing fields: {', '.join(missing)}")
        row_id = row["id"]
        if not isinstance(row_id, str) or not ID_RE.fullmatch(row_id):
            fail(f"frequency rows[{index}].id is invalid: {row_id!r}")
        if row_id in seen:
            fail(f"duplicate frequency row id: {row_id}")
        seen.add(row_id)

        low, high = row["frequency_min"], row["frequency_max"]
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (low, high)):
            fail(f"{row_id}: frequency bounds must be numbers")
        if not 0 < low < high:
            fail(f"{row_id}: frequency_min must be positive and below frequency_max")
        if row["unit"] not in ALLOWED_FREQ_UNITS:
            fail(f"{row_id}: invalid unit")

        classes = row["license_class"]
        if (
            not isinstance(classes, list)
            or not classes
            or not set(classes) <= ALLOWED_LICENSE_CLASSES
        ):
            fail(f"{row_id}: license_class must be a non-empty subset of A/B/C")

        power = row["maximum_output_power"]
        if power is not None:
            if not isinstance(power, (int, float)) or isinstance(power, bool) or power <= 0:
                fail(f"{row_id}: maximum_output_power must be positive")
            if row["power_unit"] not in {"W", "mW", "kW"}:
                fail(f"{row_id}: power value requires a valid power_unit")

        locator = row["source_locator"]
        if not isinstance(locator, dict) or not any(
            isinstance(v, str) and v.strip() for v in locator.values()
        ):
            fail(f"{row_id}: source_locator must contain a usable locator")

        if row["verification_status"] not in ALLOWED_VERIFICATION:
            fail(f"{row_id}: invalid verification_status")

        source = sources_by_id.get(row["source_id"])
        if source is None:
            fail(f"{row_id}: unknown source_id")
        if row["verification_status"] == "verified":
            if source["verification_status"] != "verified":
                fail(f"{row_id}: verified row cannot cite non-verified source")
            if source["source_type"] != "official_legal":
                fail(f"{row_id}: verified row must cite official_legal source")
            if source.get("legal_status") != "current":
                fail(f"{row_id}: verified row requires a current legal source")

        rule_id = row.get("derived_from_rule")
        if rule_id is not None:
            rule = rules_by_id.get(rule_id)
            if rule is None:
                fail(f"{row_id}: unknown derived_from_rule {rule_id}")
            params = rule.get("parameters") or {}
            expected = {
                "frequency_min_mhz": row["frequency_min"] if row["unit"] == "MHz" else None,
                "frequency_max_mhz": row["frequency_max"] if row["unit"] == "MHz" else None,
                "max_transmitter_output_power_w": power if row["power_unit"] == "W" else None,
            }
            for key, value in expected.items():
                if key in params and params[key] != value:
                    fail(f"{row_id}: {key} disagrees with rule {rule_id}")
            if "license_class" in params and params["license_class"] not in classes:
                fail(f"{row_id}: license_class disagrees with rule {rule_id}")
            if row["verification_status"] == "verified" and rule["verification_status"] != "verified":
                fail(f"{row_id}: verified row cannot derive from non-verified rule")


def main() -> int:
    source_payload = load_json(SOURCES, "source registry")
    sources = source_payload.get("sources")
    if not isinstance(sources, list):
        fail("sources must be a list")

    seen_source_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            fail(f"sources[{index}] must be an object")
        validate_source(source, index, seen_source_ids)

    sources_by_id = {source["id"]: source for source in sources}

    rule_payload = load_json(RULES, "rule registry")
    rules = rule_payload.get("rules")
    if not isinstance(rules, list):
        fail("rules must be a list")

    seen_rule_ids: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            fail(f"rules[{index}] must be an object")
        validate_rule(rule, index, seen_rule_ids, sources_by_id)

    rules_by_id = {rule["id"]: rule for rule in rules}
    table = load_json(FREQUENCY_TABLE, "frequency table")
    validate_frequency_table(table, sources_by_id, rules_by_id)

    print(
        f"PASS: validated {len(sources)} source record(s), "
        f"{len(rules)} grounded rule(s) "
        f"and {len(table['rows'])} frequency row(s) "
        f"[coverage={table['coverage_status']}]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
