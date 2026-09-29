#!/usr/bin/env python3
"""Validate official legal corroboration records.

Corroborations preserve useful official-agency evidence while remaining
strictly weaker than the canonical consolidated legal source.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CORROBORATIONS = ROOT / "data" / "legal_corroborations.json"
SOURCES = ROOT / "data" / "sources.json"
RULES = ROOT / "data" / "rules.json"
FREQUENCY_TABLE = ROOT / "data" / "frequency_table.json"

ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{2,127}$")
ALLOWED_SCOPE = {"official_corroboration_only"}
ALLOWED_ACCESS = {"unavailable_in_current_verification_path", "available"}
ALLOWED_EVIDENCE = {"exact_quote_observed", "reference_only", "publication_metadata"}


class CorroborationError(ValueError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorroborationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CorroborationError(f"{path}: root must be an object")
    return value


def official_btk_host(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host == "btk.gov.tr" or host.endswith(".btk.gov.tr"))


def source_map(payload: dict) -> dict[str, dict]:
    items = payload.get("sources")
    if not isinstance(items, list):
        raise CorroborationError("source registry must contain sources list")
    return {
        item["id"]: item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def validate_reference(record_id: str, ref: dict, seen: set[tuple[str, str]]) -> None:
    required = {"article", "evidence_kind", "locator", "summary"}
    missing = required - set(ref)
    if missing:
        raise CorroborationError(f"{record_id}: reference missing fields {sorted(missing)}")
    article = ref["article"]
    kind = ref["evidence_kind"]
    locator = ref["locator"]
    summary = ref["summary"]
    if not isinstance(article, str) or not article.strip():
        raise CorroborationError(f"{record_id}: article must be non-empty")
    if kind not in ALLOWED_EVIDENCE:
        raise CorroborationError(f"{record_id}: invalid evidence_kind {kind!r}")
    if not isinstance(locator, str) or len(locator.strip()) < 8:
        raise CorroborationError(f"{record_id}: locator is too short")
    if not isinstance(summary, str) or len(summary.strip()) < 16:
        raise CorroborationError(f"{record_id}: summary is too short")
    key = (article.strip(), kind)
    if key in seen:
        raise CorroborationError(f"{record_id}: duplicate reference {key}")
    seen.add(key)


def validate_record(record: dict, sources: dict[str, dict], seen_ids: set[str]) -> None:
    required = {
        "id",
        "canonical_source_id",
        "corroborating_publisher",
        "corroborating_url",
        "observed_date",
        "authority_scope",
        "canonical_access_status",
        "promotes_canonical_source",
        "may_ground_verified_legal_rule",
        "legal_verdicts",
        "references",
        "notes",
    }
    missing = required - set(record)
    if missing:
        raise CorroborationError(f"corroboration missing fields: {sorted(missing)}")

    record_id = record["id"]
    if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
        raise CorroborationError(f"invalid corroboration id: {record_id!r}")
    if record_id in seen_ids:
        raise CorroborationError(f"duplicate corroboration id: {record_id}")
    seen_ids.add(record_id)

    canonical_id = record["canonical_source_id"]
    canonical = sources.get(canonical_id)
    if canonical is None:
        raise CorroborationError(f"{record_id}: unknown canonical_source_id {canonical_id}")
    if canonical.get("source_type") != "official_legal":
        raise CorroborationError(f"{record_id}: canonical source must be official_legal")

    if not isinstance(record["corroborating_publisher"], str) or len(record["corroborating_publisher"].strip()) < 3:
        raise CorroborationError(f"{record_id}: invalid corroborating_publisher")
    if not official_btk_host(record["corroborating_url"]):
        raise CorroborationError(f"{record_id}: corroborating_url must be an official btk.gov.tr HTTPS URL")

    observed = record["observed_date"]
    if not isinstance(observed, str):
        raise CorroborationError(f"{record_id}: observed_date must be YYYY-MM-DD")
    try:
        date.fromisoformat(observed)
    except ValueError as exc:
        raise CorroborationError(f"{record_id}: invalid observed_date") from exc

    if record["authority_scope"] not in ALLOWED_SCOPE:
        raise CorroborationError(f"{record_id}: authority_scope must be official_corroboration_only")
    if record["canonical_access_status"] not in ALLOWED_ACCESS:
        raise CorroborationError(f"{record_id}: invalid canonical_access_status")
    if record["promotes_canonical_source"] is not False:
        raise CorroborationError(f"{record_id}: corroboration cannot promote canonical source")
    if record["may_ground_verified_legal_rule"] is not False:
        raise CorroborationError(f"{record_id}: corroboration cannot ground verified legal rules")
    if record["legal_verdicts"] is not False:
        raise CorroborationError(f"{record_id}: legal_verdicts must remain false")

    refs = record["references"]
    if not isinstance(refs, list) or not refs:
        raise CorroborationError(f"{record_id}: references must be a non-empty list")
    seen_refs: set[tuple[str, str]] = set()
    for ref in refs:
        if not isinstance(ref, dict):
            raise CorroborationError(f"{record_id}: reference must be an object")
        validate_reference(record_id, ref, seen_refs)

    if not isinstance(record["notes"], str) or len(record["notes"].strip()) < 24:
        raise CorroborationError(f"{record_id}: notes are too short")


def validate_repository(
    corroborations_payload: dict,
    sources_payload: dict,
    rules_payload: dict,
    frequency_payload: dict,
) -> int:
    if corroborations_payload.get("schema_version") != 1:
        raise CorroborationError("legal corroboration schema_version must be 1")
    records = corroborations_payload.get("records")
    if not isinstance(records, list) or not records:
        raise CorroborationError("legal corroboration registry must contain records")

    sources = source_map(sources_payload)
    source_ids = set(sources)
    corroboration_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise CorroborationError("corroboration record must be an object")
        validate_record(record, sources, corroboration_ids)

    overlap = source_ids & corroboration_ids
    if overlap:
        raise CorroborationError(f"corroboration ids must not appear in source registry: {sorted(overlap)}")

    for rule in rules_payload.get("rules", []):
        if isinstance(rule, dict) and rule.get("source_id") in corroboration_ids:
            raise CorroborationError(
                f"{rule.get('id')}: rule cannot cite corroboration record as source"
            )

    for row in frequency_payload.get("rows", []):
        if isinstance(row, dict) and row.get("source_id") in corroboration_ids:
            raise CorroborationError(
                f"{row.get('id')}: frequency row cannot cite corroboration record as source"
            )

    return len(records)


def main() -> int:
    try:
        count = validate_repository(
            load_json(CORROBORATIONS),
            load_json(SOURCES),
            load_json(RULES),
            load_json(FREQUENCY_TABLE),
        )
    except CorroborationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        f"PASS: validated {count} official legal corroboration record(s); "
        "corroboration cannot promote canonical legal authority"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
