#!/usr/bin/env python3
"""Fail-closed bilingual documentation validator.

English navigation is derivative only. The manifest pins the Git blob SHA-1
of each canonical Turkish document so a canonical edit requires explicit
translation review before CI can pass again.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "translations.json"
SOURCES = ROOT / "data" / "sources.json"
RULES = ROOT / "data" / "rules.json"


class TranslationError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TranslationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TranslationError(f"{path}: root must be an object")
    return value


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def safe_relative_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise TranslationError(f"{field} must be a non-empty string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise TranslationError(f"{field} must be a safe repository-relative path")
    return path


def registry_map(payload: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    values = payload.get(key)
    if not isinstance(values, list):
        raise TranslationError(f"registry must contain a {key} list")
    result: dict[str, dict[str, Any]] = {}
    for value in values:
        if isinstance(value, dict) and isinstance(value.get("id"), str):
            result[value["id"]] = value
    return result


def validate_id_list(
    record: dict[str, Any],
    field: str,
    registry: dict[str, dict[str, Any]],
    *,
    require_nonempty: bool,
) -> list[str]:
    values = record.get(field)
    if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
        raise TranslationError(f"{record.get('id')}: {field} must be a string list")
    if len(values) != len(set(values)):
        raise TranslationError(f"{record.get('id')}: duplicate {field}")
    if require_nonempty and not values:
        raise TranslationError(f"{record.get('id')}: {field} must not be empty")
    for value in values:
        item = registry.get(value)
        if item is None:
            raise TranslationError(f"{record.get('id')}: unknown {field} id {value}")
        if item.get("verification_status") != "verified":
            raise TranslationError(
                f"{record.get('id')}: {field} id {value} is not verified; "
                "English navigation cannot promote pending/unverified authority"
            )
    return values


def validate_record(
    record: dict[str, Any],
    sources: dict[str, dict[str, Any]],
    rules: dict[str, dict[str, Any]],
    root: Path,
) -> None:
    required = {
        "id",
        "canonical_path",
        "translation_path",
        "language",
        "translation_kind",
        "canonical_blob_sha1",
        "source_ids",
        "rule_ids",
        "legal_verdicts",
        "canonical_controls",
    }
    missing = required - set(record)
    if missing:
        raise TranslationError(f"translation record missing fields: {sorted(missing)}")

    record_id = record["id"]
    if not isinstance(record_id, str) or not record_id:
        raise TranslationError("translation id must be a non-empty string")
    if record["language"] != "en":
        raise TranslationError(f"{record_id}: only English navigation is supported in v1")
    if record["translation_kind"] != "navigation":
        raise TranslationError(f"{record_id}: translation_kind must be navigation")
    if record["legal_verdicts"] is not False:
        raise TranslationError(f"{record_id}: legal_verdicts must remain false")
    if record["canonical_controls"] is not True:
        raise TranslationError(f"{record_id}: canonical_controls must remain true")

    canonical_rel = safe_relative_path(record["canonical_path"], "canonical_path")
    translation_rel = safe_relative_path(record["translation_path"], "translation_path")
    if canonical_rel == translation_rel:
        raise TranslationError(f"{record_id}: canonical and translation paths must differ")

    canonical = root / canonical_rel
    translation = root / translation_rel
    if not canonical.is_file():
        raise TranslationError(f"{record_id}: canonical file missing: {canonical_rel}")
    if not translation.is_file():
        raise TranslationError(f"{record_id}: translation file missing: {translation_rel}")

    expected_sha = record["canonical_blob_sha1"]
    if (
        not isinstance(expected_sha, str)
        or len(expected_sha) != 40
        or any(ch not in "0123456789abcdef" for ch in expected_sha.lower())
    ):
        raise TranslationError(f"{record_id}: canonical_blob_sha1 must be a 40-char hex Git blob SHA-1")

    actual_sha = git_blob_sha1(canonical)
    if actual_sha != expected_sha.lower():
        raise TranslationError(
            f"{record_id}: RETRANSLATION_REQUIRED canonical blob changed "
            f"expected={expected_sha.lower()} actual={actual_sha}"
        )

    source_ids = validate_id_list(record, "source_ids", sources, require_nonempty=True)
    rule_ids = validate_id_list(record, "rule_ids", rules, require_nonempty=False)

    text = translation.read_text(encoding="utf-8")
    lower = text.lower()
    if str(canonical_rel) not in text:
        raise TranslationError(f"{record_id}: translation must name canonical_path {canonical_rel}")
    if "navigation/translation only" not in lower:
        raise TranslationError(f"{record_id}: translation-only disclaimer missing")
    if "does not create or change legal permission" not in lower:
        raise TranslationError(f"{record_id}: legal-permission disclaimer missing")
    if "legal_verdicts=true" in lower or "legal_verdicts: true" in lower:
        raise TranslationError(f"{record_id}: translation text attempts to enable legal verdicts")

    for value in source_ids + rule_ids:
        if value not in text:
            raise TranslationError(f"{record_id}: translation text is missing canonical id {value}")


def validate_repository(
    manifest_payload: dict[str, Any],
    sources_payload: dict[str, Any],
    rules_payload: dict[str, Any],
    root: Path = ROOT,
) -> int:
    if manifest_payload.get("schema_version") != 1:
        raise TranslationError("translation manifest schema_version must be 1")
    if manifest_payload.get("canonical_language") != "tr":
        raise TranslationError("canonical_language must be tr")

    records = manifest_payload.get("translations")
    if not isinstance(records, list) or not records:
        raise TranslationError("translation manifest must contain at least one translation")

    sources = registry_map(sources_payload, "sources")
    rules = registry_map(rules_payload, "rules")
    seen_ids: set[str] = set()
    seen_targets: set[str] = set()

    for record in records:
        if not isinstance(record, dict):
            raise TranslationError("translation record must be an object")
        record_id = record.get("id")
        if record_id in seen_ids:
            raise TranslationError(f"duplicate translation id: {record_id}")
        target = record.get("translation_path")
        if target in seen_targets:
            raise TranslationError(f"duplicate translation target: {target}")
        validate_record(record, sources, rules, root)
        seen_ids.add(record_id)
        seen_targets.add(target)

    return len(records)


def main() -> int:
    try:
        count = validate_repository(load_json(MANIFEST), load_json(SOURCES), load_json(RULES))
    except TranslationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: validated {count} English navigation translation(s); canonical Turkish/source-backed documents control")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
