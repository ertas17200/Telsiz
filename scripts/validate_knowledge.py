#!/usr/bin/env python3
"""Fail-closed validator for the Telsiz source registry.

Uses only the Python standard library so it can run in a clean GitHub Actions
runner without installing dependencies.
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
ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{2,63}$")
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
    if digest is not None and not SHA_RE.fullmatch(digest):
        fail(f"{source_id}: invalid content_sha256")

    if source["source_type"] == "official_legal":
        if not legal_status:
            fail(f"{source_id}: official_legal requires legal_status")
        if source["verification_status"] == "verified" and legal_status == "unknown":
            fail(f"{source_id}: verified current-use legal source cannot have unknown status")


def main() -> int:
    if not SOURCES.exists():
        fail(f"missing registry: {SOURCES}")

    try:
        payload = json.loads(SOURCES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse source registry: {exc}")

    if payload.get("schema_version") != 1:
        fail("schema_version must be 1")

    sources = payload.get("sources")
    if not isinstance(sources, list):
        fail("sources must be a list")

    seen_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            fail(f"sources[{index}] must be an object")
        validate_source(source, index, seen_ids)

    print(f"PASS: validated {len(sources)} source record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
