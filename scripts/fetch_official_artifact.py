#!/usr/bin/env python3
"""Fetch a registered official artifact and emit byte-level observation evidence.

This command is deliberately observation-only. It never mutates data/sources.json
or data/artifacts.json and therefore cannot silently bind a newly observed hash.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import artifact_gate as gate

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAX_BYTES = 25 * 1024 * 1024

MIME_SUFFIX = {
    "application/pdf": ".pdf",
    "text/html": ".html",
    "application/json": ".json",
}


def suffix_for_mime(mime_type: str) -> str:
    try:
        return MIME_SUFFIX[mime_type]
    except KeyError as exc:
        raise gate.GateError(f"unsupported artifact MIME type for suffix: {mime_type}") from exc
USER_AGENT = "TelsizArtifactGate/1.0 (+https://github.com/ertas17200/Telsiz)"


def artifact_map(payload: dict) -> dict[str, dict]:
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise gate.GateError("artifact registry must contain an artifacts list")
    result: dict[str, dict] = {}
    for record in artifacts:
        if not isinstance(record, dict) or not isinstance(record.get("source_id"), str):
            raise gate.GateError("artifact registry contains an invalid record")
        if record["source_id"] in result:
            raise gate.GateError(f"duplicate artifact source_id: {record['source_id']}")
        result[record["source_id"]] = record
    return result


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise gate.GateError("canonical artifact URL must use HTTPS")
    return parsed.scheme.lower(), parsed.hostname.lower(), parsed.port


def _same_origin(canonical_url: str, final_url: str) -> bool:
    return _origin(canonical_url) == _origin(final_url)


def fetch_registered_artifact(
    source: dict,
    artifact: dict,
    destination: Path,
    *,
    timeout_seconds: float = 30.0,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        raise gate.GateError("max_bytes must be a positive integer")
    if timeout_seconds <= 0:
        raise gate.GateError("timeout_seconds must be positive")

    canonical_url = source.get("url")
    if not isinstance(canonical_url, str):
        raise gate.GateError("source canonical URL is missing")
    _origin(canonical_url)

    if artifact.get("canonical_url") != canonical_url:
        raise gate.GateError("artifact canonical_url does not match source registry")

    request = Request(
        canonical_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": artifact["expected_mime_type"],
        },
        method="GET",
    )

    try:
        response_context = urlopen(request, timeout=timeout_seconds)
    except Exception as exc:
        raise gate.GateError(f"canonical artifact download failed: {exc}") from exc

    with response_context as response:
        http_status = getattr(response, "status", None)
        if http_status is None and hasattr(response, "getcode"):
            http_status = response.getcode()
        if http_status != 200:
            raise gate.GateError(
                f"canonical artifact HTTP status must be 200, got {http_status!r}"
            )

        final_url = response.geturl()
        if not _same_origin(canonical_url, final_url):
            raise gate.GateError(
                f"canonical artifact redirected to a different origin: {final_url}"
            )

        headers = response.headers
        content_type = (
            headers.get_content_type()
            if hasattr(headers, "get_content_type")
            else str(headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
        )
        expected_mime = artifact["expected_mime_type"]
        if content_type != expected_mime:
            raise gate.GateError(
                f"HTTP Content-Type mismatch: expected {expected_mime}, got {content_type or 'missing'}"
            )

        content_length_raw = headers.get("Content-Length")
        if content_length_raw:
            try:
                content_length = int(content_length_raw)
            except ValueError as exc:
                raise gate.GateError("invalid HTTP Content-Length") from exc
            if content_length <= 0:
                raise gate.GateError("HTTP Content-Length must be positive")
            if content_length > max_bytes:
                raise gate.GateError(
                    f"artifact exceeds max_bytes before download: {content_length} > {max_bytes}"
                )

        total = 0
        with destination.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise gate.GateError(
                        f"artifact exceeded max_bytes during download: {total} > {max_bytes}"
                    )
                handle.write(chunk)

    if total <= 0:
        raise gate.GateError("canonical artifact download returned zero bytes")

    return {
        "canonical_url": canonical_url,
        "final_url": final_url,
        "http_status": http_status,
        "http_content_type": content_type,
        "downloaded_bytes": total,
    }


def observe_source(
    source_id: str,
    fetched_at: str,
    *,
    timeout_seconds: float = 30.0,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> dict:
    sources_payload = gate.load_json(gate.SOURCES)
    artifacts_payload = gate.load_json(gate.ARTIFACTS)
    gate.validate_registry(artifacts_payload, sources_payload)

    sources = gate.source_map(sources_payload)
    artifacts = artifact_map(artifacts_payload)
    source = sources.get(source_id)
    artifact = artifacts.get(source_id)
    if source is None:
        raise gate.GateError(f"unknown source_id: {source_id}")
    if artifact is None:
        raise gate.GateError(f"source has no artifact registry record: {source_id}")

    suffix = suffix_for_mime(artifact["expected_mime_type"])
    with tempfile.TemporaryDirectory(prefix="telsiz-artifact-") as tmp:
        local_path = Path(tmp) / f"artifact{suffix}"
        retrieval = fetch_registered_artifact(
            source,
            artifact,
            local_path,
            timeout_seconds=timeout_seconds,
            max_bytes=max_bytes,
        )
        observation = gate.build_observation(
            source=source,
            path=local_path,
            fetched_at=fetched_at,
            expected_mime_type=artifact["expected_mime_type"],
        )

    observation["retrieval"] = retrieval
    observation["binding_action"] = "REVIEW_REQUIRED_NO_AUTOMATIC_REGISTRY_MUTATION"
    return observation


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Fetch a registered canonical artifact and emit review-only hash evidence."
    )
    p.add_argument("--source-id", required=True)
    p.add_argument("--fetched-at", required=True)
    p.add_argument("--timeout-seconds", type=float, default=30.0)
    p.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    p.add_argument("--output")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        observation = observe_source(
            args.source_id,
            args.fetched_at,
            timeout_seconds=args.timeout_seconds,
            max_bytes=args.max_bytes,
        )
    except gate.GateError as exc:
        print(f"ARTIFACT_OBSERVATION=HOLD reason={exc}")
        return 1

    output = json.dumps(observation, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)

    if observation["change_status"] == gate.SOURCE_CHANGED:
        print("ARTIFACT_OBSERVATION=SOURCE_CHANGED")
        return 2

    print(
        "ARTIFACT_OBSERVATION=PASS "
        f"source_id={observation['source_id']} "
        f"change_status={observation['change_status']} "
        f"size_bytes={observation['size_bytes']} "
        f"sha256={observation['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
