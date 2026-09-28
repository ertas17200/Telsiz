#!/usr/bin/env python3
"""Lookup a partial TRAC repeater operational snapshot without inferring permission."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "repeaters.json"


def load_registry(path: Path = REGISTRY) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be an ISO-8601 UTC value ending in Z")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("invalid ISO-8601 timestamp") from exc
    return dt.astimezone(timezone.utc)


def snapshot_freshness(
    as_of: str,
    registry: dict | None = None,
) -> dict:
    data = registry or load_registry()
    observed = _parse_utc(data["observed_at"])
    now = _parse_utc(as_of)
    if now < observed:
        raise ValueError("as_of cannot be before the snapshot observation time")
    age_days = (now - observed).total_seconds() / 86400
    threshold = data["freshness_policy"]["stale_after_days"]
    status = "FRESH" if age_days <= threshold else "STALE"
    return {
        "status": status,
        "age_days": age_days,
        "stale_after_days": threshold,
        "policy_origin": data["freshness_policy"]["policy_origin"],
    }


def search_repeaters(
    *,
    branch: str | None = None,
    site: str | None = None,
    band: str | None = None,
    operational_status: str | None = None,
    registry: dict | None = None,
) -> dict:
    data = registry or load_registry()
    records = list(data["records"])

    def norm(value: str | None) -> str | None:
        return value.strip().casefold() if isinstance(value, str) and value.strip() else None

    q_branch = norm(branch)
    q_site = norm(site)
    q_band = band.strip().upper() if isinstance(band, str) and band.strip() else None
    q_status = norm(operational_status)

    if q_band is not None and q_band not in {"VHF", "UHF"}:
        raise ValueError("band must be VHF or UHF")

    results = []
    for record in records:
        if q_branch is not None and q_branch not in record["branch"].casefold():
            continue
        if q_site is not None and q_site not in record["site"].casefold():
            continue
        if q_band is not None and record["band"] != q_band:
            continue
        if q_status is not None and record["operational_status"].casefold() != q_status:
            continue
        item = dict(record)
        item["legal_verdict"] = None
        results.append(item)

    return {
        "coverage_status": data["coverage_status"],
        "coverage_note": data["coverage_note"],
        "snapshot_id": data["snapshot_id"],
        "observed_at": data["observed_at"],
        "operational_source_id": data["operational_source_id"],
        "legal_authority_source_id": data["legal_authority_source_id"],
        "results": results,
        "legal_verdict": None,
        "permission_note": data["permission_semantics"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search a partial TRAC repeater snapshot without inferring official permission."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search")
    search.add_argument("--branch")
    search.add_argument("--site")
    search.add_argument("--band", choices=("VHF", "UHF"))
    search.add_argument("--status")

    fresh = sub.add_parser("freshness")
    fresh.add_argument("--as-of", required=True, help="UTC ISO timestamp ending in Z")

    args = parser.parse_args()
    if args.command == "freshness":
        result = snapshot_freshness(args.as_of)
    else:
        result = search_repeaters(
            branch=args.branch,
            site=args.site,
            band=args.band,
            operational_status=args.status,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
