#!/usr/bin/env python3
"""Validate data/digital_modes.json (FT8/FT4 technical parameters).

The file carries community-tier protocol parameters pinned to an exact
open-source commit. This validator enforces provenance (commit, per-file
Git blob SHA-1 and SHA-256) and the internal arithmetic of the protocol
structure, so a transcription error cannot pass silently:

- data + sync + ramp symbols == total symbols;
- data symbols x bits per symbol == LDPC codeword length (174);
- the full CRC polynomial == (1 << width) | polynomial without MSB;
- one transmission fits inside its time slot.

``--verify-clone PATH`` additionally checks a local clone at the pinned
commit: file hashes and every cited value/line must match.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "digital_modes.json"
SOURCES = ROOT / "data" / "sources.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
LOCATOR_RE = re.compile(r"^(?P<path>[\w./-]+)#L(?P<start>\d+)(?:-L(?P<end>\d+))?$")
MODE_FIELDS = (
    "symbol_period_s", "slot_time_s", "bits_per_symbol", "data_symbols",
    "sync_groups", "sync_group_length", "ramp_symbols", "total_symbols",
)


class DigitalModesError(ValueError):
    pass


def fail(message: str) -> None:
    raise DigitalModesError(message)


def derived(mode: dict) -> dict:
    """Values computed from the source parameters (never stored)."""
    period = mode["symbol_period_s"]
    return {
        "tones": 2 ** mode["bits_per_symbol"],
        "tone_spacing_hz": 1 / period,
        "symbol_rate_baud": 1 / period,
        "transmission_s": mode["total_symbols"] * period,
        "sync_symbols": mode["sync_groups"] * mode["sync_group_length"],
    }


def validate(payload: dict, sources: dict) -> None:
    if payload.get("schema_version") != 1:
        fail("schema_version must be 1")
    source = sources.get(payload.get("source_id"))
    if source is None:
        fail("source_id is not registered in data/sources.json")
    if source["verification_status"] != "verified":
        fail("source provenance must be verified")
    if source["source_type"] != "community" or payload.get("trust_tier") != "community_independent_implementation":
        fail("independent implementation must stay in the community trust tier")
    if not isinstance(payload.get("trust_note"), str) or "doğrulama bekler" not in payload["trust_note"]:
        fail("trust_note must state that authoritative corroboration is pending")

    prov = payload.get("provenance") or {}
    if not isinstance(prov.get("repository"), str) or not prov["repository"].startswith("https://github.com/"):
        fail("provenance.repository must be an https GitHub URL")
    if not HEX40.fullmatch(str(prov.get("commit", ""))):
        fail("provenance.commit must be a 40-hex commit SHA")
    if prov["commit"] not in source.get("url", ""):
        fail("source url must pin the same commit")
    files = {f.get("path"): f for f in prov.get("files", [])}
    if not files:
        fail("provenance.files is required")
    for path, item in files.items():
        if not HEX40.fullmatch(str(item.get("git_blob_sha1", ""))):
            fail(f"{path}: git_blob_sha1 must be 40-hex (not PENDING)")
        if not HEX64.fullmatch(str(item.get("sha256", ""))):
            fail(f"{path}: sha256 must be 64-hex (not PENDING)")

    def check_locators(locators: dict, fields: tuple[str, ...] | list[str], owner: str) -> None:
        for field in fields:
            locator = locators.get(field)
            match = LOCATOR_RE.fullmatch(str(locator))
            if not match:
                fail(f"{owner}.{field}: locator must look like path#Lnn")
            if match["path"] not in files:
                fail(f"{owner}.{field}: locator file {match['path']} is not in provenance.files")

    shared = payload.get("shared") or {}
    ldpc_n, ldpc_k, width = shared.get("ldpc_n"), shared.get("ldpc_k"), shared.get("crc_width")
    if not all(isinstance(v, int) and v > 0 for v in (ldpc_n, ldpc_k, width)) or ldpc_k >= ldpc_n:
        fail("shared LDPC/CRC sizes must be positive integers with k < n")
    poly_low = int(shared.get("crc_polynomial_without_msb", "x"), 16)
    poly_full = int(shared.get("crc_polynomial_full", "x"), 16)
    if poly_full != (1 << width) | poly_low:
        fail("crc_polynomial_full must equal (1 << crc_width) | crc_polynomial_without_msb")
    check_locators(shared.get("locators", {}), ["ldpc_n", "ldpc_k", "crc_width",
                                                 "crc_polynomial_without_msb", "crc_polynomial_full"], "shared")

    seen = set()
    for mode in payload.get("modes", []):
        mid = mode.get("id")
        if mid in seen:
            fail(f"duplicate mode {mid}")
        seen.add(mid)
        for field in MODE_FIELDS:
            value = mode.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                fail(f"{mid}.{field} must be a non-negative number")
        d = derived(mode)
        if mode["data_symbols"] + d["sync_symbols"] + mode["ramp_symbols"] != mode["total_symbols"]:
            fail(f"{mid}: data + sync + ramp symbols must equal total_symbols")
        if mode["data_symbols"] * mode["bits_per_symbol"] != ldpc_n:
            fail(f"{mid}: data_symbols x bits_per_symbol must equal the LDPC codeword length")
        if not 0 < d["transmission_s"] < mode["slot_time_s"]:
            fail(f"{mid}: transmission must fit inside the time slot")
        check_locators(mode.get("locators", {}),
                       [f for f in MODE_FIELDS if f != "ramp_symbols" or mode["ramp_symbols"]], mid)
    if seen != {"FT8", "FT4"}:
        fail("modes must be exactly FT8 and FT4")
    if not payload.get("not_stated_by_source"):
        fail("not_stated_by_source must list what the source does not establish")


def _cited_line(clone: Path, locator: str) -> str:
    match = LOCATOR_RE.fullmatch(locator)
    lines = (clone / match["path"]).read_text(encoding="utf-8").splitlines()
    start = int(match["start"])
    end = int(match["end"] or start)
    return "\n".join(lines[start - 1:end])


def verify_clone(payload: dict, clone: Path) -> None:
    head = subprocess.run(["git", "-C", str(clone), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    if head != payload["provenance"]["commit"]:
        fail(f"clone HEAD {head} != pinned commit")
    for item in payload["provenance"]["files"]:
        data = (clone / item["path"]).read_bytes()
        blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        if blob != item["git_blob_sha1"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            fail(f"{item['path']}: file hash differs from pinned provenance")
    for mode in payload["modes"]:
        for field, locator in mode["locators"].items():
            line = _cited_line(clone, locator)
            value = mode[field]
            token = {"bits_per_symbol": f"encoding {value} bits"}.get(field, f"{value:g}" if isinstance(value, float) else str(value))
            if field == "symbol_period_s":
                token = f"{value:.3f}f"
            if field == "slot_time_s":
                token = f"{value:.1f}f"
            if token not in line:
                fail(f"{mode['id']}.{field}: '{token}' not found at {locator}")
    shared = payload["shared"]
    for field, token in (("ldpc_n", f"({shared['ldpc_n']})"), ("ldpc_k", f"({shared['ldpc_k']})"),
                         ("crc_width", f"({shared['crc_width']})"),
                         ("crc_polynomial_without_msb", shared["crc_polynomial_without_msb"])):
        if token.lower() not in _cited_line(clone, shared["locators"][field]).lower():
            fail(f"shared.{field}: '{token}' not found at {shared['locators'][field]}")
    if shared["crc_polynomial_full"].lower() not in _cited_line(clone, shared["locators"]["crc_polynomial_full"]).lower():
        fail("shared.crc_polynomial_full not found at its locator")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--verify-clone", type=Path, help="local clone of the pinned repository")
    args = parser.parse_args(argv)
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in json.loads(SOURCES.read_text(encoding="utf-8"))["sources"]}
    try:
        validate(payload, sources)
        if args.verify_clone:
            verify_clone(payload, args.verify_clone)
    except DigitalModesError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    extra = " and matched the pinned clone" if args.verify_clone else ""
    print(f"PASS: validated {len(payload['modes'])} digital mode record(s) (community tier, commit-pinned){extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
