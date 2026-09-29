#!/usr/bin/env python3
"""Fetch one canonical official artifact and emit byte-level evidence.

This command never mutates the repository registries. It is an acquisition
probe only. Promotion/binding is a separate reviewed step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES = 25 * 1024 * 1024
USER_AGENT = "Telsiz-Official-Artifact-Probe/1.0 (+https://github.com/ertas17200/Telsiz)"


def fetch(url: str, output: Path, timeout: int) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.1",
        },
        method="GET",
    )
    ctx = ssl.create_default_context()
    hasher = hashlib.sha256()
    size = 0
    first = b""

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = getattr(resp, "status", None)
            final_url = resp.geturl()
            content_type = (resp.headers.get_content_type() or "").lower()
            if status != 200:
                raise RuntimeError(f"HTTP status must be 200, got {status}")
            if final_url != url:
                raise RuntimeError(f"canonical URL redirected: final_url={final_url}")

            with output.open("wb") as handle:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    if not first:
                        first = chunk[:16]
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise RuntimeError(f"artifact exceeds {MAX_BYTES} bytes")
                    hasher.update(chunk)
                    handle.write(chunk)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"download failed: {type(exc).__name__}: {exc}") from exc

    if size <= 0:
        raise RuntimeError("downloaded artifact is empty")
    if not first.startswith(b"%PDF-"):
        raise RuntimeError("downloaded artifact lacks PDF signature")
    if content_type not in {"application/pdf", "application/octet-stream"}:
        raise RuntimeError(f"unexpected Content-Type: {content_type}")

    return {
        "schema_version": 1,
        "source_id": "TR.BTK.FTM.TECH.2022-IK-SYD-245",
        "canonical_url": url,
        "final_url": final_url,
        "http_status": 200,
        "content_type": content_type,
        "size_bytes": size,
        "sha256": "sha256:" + hasher.hexdigest(),
        "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "pdf_signature": "PASS",
        "acquisition_status": "BYTE_ARTIFACT_OBSERVED",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--evidence", required=True)
    p.add_argument("--timeout", type=int, default=30)
    args = p.parse_args()

    output = Path(args.output)
    evidence = Path(args.evidence)
    try:
        result = fetch(args.url, output, args.timeout)
    except Exception as exc:
        print(f"BTK_BYTE_PROBE=HOLD reason={exc}", file=sys.stderr)
        return 2

    evidence.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("BTK_BYTE_PROBE=PASS")
    for key in ("source_id", "http_status", "content_type", "size_bytes", "sha256", "fetched_at"):
        print(f"{key.upper()}={result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
