#!/usr/bin/env python3
"""Fail-closed official-source artifact gate.

The gate is deliberately byte-oriented. A rendered page, parsed text, or
successful browser view is not a substitute for the raw artifact bytes when
binding a content hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources.json"
ARTIFACTS = ROOT / "data" / "artifacts.json"

SHA_PREFIX = "sha256:"
AWAITING = "awaiting_bytes"
VERIFIED = "verified_bytes"
CHANGE_UNKNOWN = "UNKNOWN"
HASH_BIND_REQUIRED = "HASH_OBSERVED_BIND_REQUIRED"
UNCHANGED = "UNCHANGED"
SOURCE_CHANGED = "SOURCE_CHANGED"


class GateError(ValueError):
    pass


def normalize_sha(value: str | None) -> str | None:
    if value is None:
        return None
    raw = value.removeprefix(SHA_PREFIX).lower()
    if len(raw) != 64 or any(ch not in "0123456789abcdef" for ch in raw):
        raise GateError("invalid SHA-256 digest")
    return SHA_PREFIX + raw


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return SHA_PREFIX + digest.hexdigest()


def inspect_file(path: Path, expected_mime_type: str) -> tuple[int, str, str]:
    if not path.is_file():
        raise GateError("artifact path must be an existing regular file")
    size = path.stat().st_size
    if size <= 0:
        raise GateError("artifact must be non-empty")

    head = path.read_bytes()[:16]
    if expected_mime_type == "application/pdf" and not head.startswith(b"%PDF-"):
        raise GateError("artifact does not have a PDF signature")

    guessed = mimetypes.guess_type(path.name)[0]
    mime_type = "application/pdf" if head.startswith(b"%PDF-") else (guessed or "application/octet-stream")
    if mime_type != expected_mime_type:
        raise GateError(f"artifact MIME mismatch: expected {expected_mime_type}, got {mime_type}")

    return size, mime_type, sha256_file(path)


def source_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise GateError("source registry must contain a sources list")
    return {item["id"]: item for item in sources if isinstance(item, dict) and isinstance(item.get("id"), str)}


def validate_record(record: dict[str, Any], sources: dict[str, dict[str, Any]]) -> None:
    required = {
        "source_id",
        "canonical_url",
        "expected_mime_type",
        "artifact_status",
        "fetched_at",
        "size_bytes",
        "sha256",
        "change_status",
        "reverify_required",
        "notes",
    }
    missing = required - set(record)
    if missing:
        raise GateError(f"artifact record missing fields: {sorted(missing)}")

    source = sources.get(record["source_id"])
    if source is None:
        raise GateError(f"unknown artifact source_id: {record['source_id']}")
    if record["canonical_url"] != source.get("url"):
        raise GateError(f"{record['source_id']}: canonical_url does not match source registry")
    if record["expected_mime_type"] not in {"application/pdf", "text/html", "application/json"}:
        raise GateError(f"{record['source_id']}: unsupported expected_mime_type")

    status = record["artifact_status"]
    if status == AWAITING:
        if any(record.get(key) is not None for key in ("fetched_at", "size_bytes", "sha256")):
            raise GateError(f"{record['source_id']}: awaiting_bytes must not carry byte evidence")
        if record["change_status"] != CHANGE_UNKNOWN:
            raise GateError(f"{record['source_id']}: awaiting_bytes change_status must be UNKNOWN")
        if record["reverify_required"] is not True:
            raise GateError(f"{record['source_id']}: awaiting_bytes must require reverification")
        return

    if status != VERIFIED:
        raise GateError(f"{record['source_id']}: invalid artifact_status")

    if not isinstance(record["fetched_at"], str):
        raise GateError(f"{record['source_id']}: verified_bytes requires fetched_at")
    try:
        datetime.fromisoformat(record["fetched_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise GateError(f"{record['source_id']}: invalid fetched_at") from exc

    if not isinstance(record["size_bytes"], int) or isinstance(record["size_bytes"], bool) or record["size_bytes"] <= 0:
        raise GateError(f"{record['source_id']}: verified_bytes requires positive size_bytes")

    observed = normalize_sha(record["sha256"])
    known = normalize_sha(source.get("content_sha256"))
    if known is None:
        expected_change = HASH_BIND_REQUIRED
        expected_reverify = True
    elif observed == known:
        expected_change = UNCHANGED
        expected_reverify = False
    else:
        expected_change = SOURCE_CHANGED
        expected_reverify = True

    if record["change_status"] != expected_change:
        raise GateError(
            f"{record['source_id']}: change_status must be {expected_change} for the observed/source hash state"
        )
    if record["reverify_required"] is not expected_reverify:
        raise GateError(
            f"{record['source_id']}: reverify_required must be {expected_reverify} for {expected_change}"
        )


def validate_registry(artifacts_payload: dict[str, Any], sources_payload: dict[str, Any]) -> int:
    if artifacts_payload.get("schema_version") != 1:
        raise GateError("artifact registry schema_version must be 1")
    artifacts = artifacts_payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise GateError("artifact registry must contain an artifacts list")

    sources = source_map(sources_payload)
    seen: set[str] = set()
    for record in artifacts:
        if not isinstance(record, dict):
            raise GateError("artifact record must be an object")
        source_id = record.get("source_id")
        if source_id in seen:
            raise GateError(f"duplicate artifact source_id: {source_id}")
        validate_record(record, sources)
        seen.add(source_id)
    return len(artifacts)


def build_observation(
    source: dict[str, Any],
    path: Path,
    fetched_at: str,
    expected_mime_type: str,
) -> dict[str, Any]:
    size, mime_type, digest = inspect_file(path, expected_mime_type)
    known = normalize_sha(source.get("content_sha256"))
    if known is None:
        change_status = HASH_BIND_REQUIRED
        reverify_required = True
    elif digest == known:
        change_status = UNCHANGED
        reverify_required = False
    else:
        change_status = SOURCE_CHANGED
        reverify_required = True

    return {
        "source_id": source["id"],
        "canonical_url": source["url"],
        "expected_mime_type": expected_mime_type,
        "artifact_status": VERIFIED,
        "fetched_at": fetched_at,
        "size_bytes": size,
        "sha256": digest,
        "change_status": change_status,
        "reverify_required": reverify_required,
        "notes": "Generated from byte-for-byte local artifact evidence. Bind the observed hash to the source registry only after provenance review.",
        "observed_mime_type": mime_type,
        "file_name": path.name,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateError(f"{path}: root must be an object")
    return value


def command_validate_registry() -> int:
    count = validate_registry(load_json(ARTIFACTS), load_json(SOURCES))
    print(f"PASS: validated {count} official artifact record(s)")
    return 0


def command_verify(args: argparse.Namespace) -> int:
    sources = source_map(load_json(SOURCES))
    source = sources.get(args.source_id)
    if source is None:
        raise GateError(f"unknown source_id: {args.source_id}")

    record = build_observation(
        source=source,
        path=Path(args.file),
        fetched_at=args.fetched_at,
        expected_mime_type=args.mime_type,
    )
    output = json.dumps(record, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    if record["change_status"] == SOURCE_CHANGED:
        return 2
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("validate-registry")

    verify = sub.add_parser("verify-file")
    verify.add_argument("--source-id", required=True)
    verify.add_argument("--file", required=True)
    verify.add_argument("--fetched-at", required=True)
    verify.add_argument("--mime-type", default="application/pdf")
    verify.add_argument("--output")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "validate-registry":
            return command_validate_registry()
        if args.command == "verify-file":
            return command_verify(args)
    except GateError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
