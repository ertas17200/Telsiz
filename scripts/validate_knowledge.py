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

    print(
        f"PASS: validated {len(sources)} source record(s) "
        f"and {len(rules)} grounded rule(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
