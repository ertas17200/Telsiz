#!/usr/bin/env python3
"""Validate data/digital_voice.json (DMR / D-STAR / YSF frame parameters).

The file records factual frame parameters observed in an independent
open-source digital-voice host (MMDVMHost), pinned to an exact commit. No
source code is copied. Each parameter carries a ``path#Lnn`` locator, the
identifier (``token``) on that line and the literal right-hand side.

Checks without a clone: provenance format, community tier, literal ==
value (integer expressions and byte arrays are re-parsed), and internal
arithmetic:

- DMR: frame bits == frame bytes x 8; voice payload + sync == frame bits;
  voice payload divides evenly into the AMBE blocks; every 7-byte sync
  pattern fits the sync mask and holds exactly the sync-length bits;
- D-STAR: voice + slow-data bytes == frame bytes;
- YSF: sync array length == declared sync length.

``--verify-clone PATH`` re-checks file hashes and every token/literal at
its locator.
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
DATA = ROOT / "data" / "digital_voice.json"
SOURCES = ROOT / "data" / "sources.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
LOCATOR_RE = re.compile(r"^(?P<path>[\w./-]+)#L(?P<start>\d+)$")
INT_EXPR_RE = re.compile(r"^\d+U?(?:\s*\*\s*\d+U?)*$")
MODES = {"DMR", "D-STAR", "YSF"}
DMR_SYNCS = ("dmr_sync_bs_voice", "dmr_sync_bs_data", "dmr_sync_ms_voice", "dmr_sync_ms_data")
REQUIRED = {
    "dmr_frame_bits", "dmr_frame_bytes", "dmr_sync_bits", "dmr_voice_payload_bits",
    "dmr_ambe_frames_per_burst", *DMR_SYNCS, "dmr_sync_mask",
    "dstar_header_bytes", "dstar_frame_bytes", "dstar_voice_bytes", "dstar_slow_data_bytes", "dstar_sync",
    "ysf_frame_bytes", "ysf_sync", "ysf_sync_bytes",
}


class DigitalVoiceError(ValueError):
    pass


def fail(message: str) -> None:
    raise DigitalVoiceError(message)


def literal_value(literal: str) -> int | list[int]:
    """Parse an unsigned integer expression (``108U * 2U``) or a byte list."""
    if INT_EXPR_RE.fullmatch(literal):
        result = 1
        for factor in literal.split("*"):
            result *= int(factor.strip().rstrip("U"))
        return result
    items = [item.strip() for item in literal.split(",")]
    if not items or not all(re.fullmatch(r"0x[0-9A-Fa-f]{2}U?", item) for item in items):
        raise DigitalVoiceError(f"unsupported literal {literal!r}")
    return [int(item.rstrip("U"), 16) for item in items]


def sync_hex(pattern: list[int]) -> str:
    """The 48-bit DMR sync held in the middle 12 nibbles of the 7-byte array."""
    return "".join(f"{b:02X}" for b in pattern)[1:13]


def values(payload: dict) -> dict:
    return {p["id"]: p["value"] for p in payload["parameters"]}


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
    if "doğrulama bekler" not in str(payload.get("trust_note", "")):
        fail("trust_note must state that authoritative corroboration is pending")

    prov = payload.get("provenance") or {}
    if not str(prov.get("repository", "")).startswith("https://github.com/"):
        fail("provenance.repository must be an https GitHub URL")
    if not HEX40.fullmatch(str(prov.get("commit", ""))):
        fail("provenance.commit must be a 40-hex commit SHA")
    if prov["commit"] not in source.get("url", ""):
        fail("source url must pin the same commit")
    if not prov.get("license"):
        fail("provenance.license is required")
    files = {f.get("path"): f for f in prov.get("files", [])}
    if not files:
        fail("provenance.files is required")
    for path, item in files.items():
        if not HEX40.fullmatch(str(item.get("git_blob_sha1", ""))):
            fail(f"{path}: git_blob_sha1 must be 40-hex")
        if not HEX64.fullmatch(str(item.get("sha256", ""))):
            fail(f"{path}: sha256 must be 64-hex")

    seen = set()
    for param in payload.get("parameters", []):
        pid = param.get("id")
        if pid in seen:
            fail(f"duplicate parameter {pid}")
        seen.add(pid)
        if param.get("mode") not in MODES:
            fail(f"{pid}: mode must be one of {sorted(MODES)}")
        for key in ("meaning", "token", "literal"):
            if not isinstance(param.get(key), str) or not param[key].strip():
                fail(f"{pid}: {key} is required")
        match = LOCATOR_RE.fullmatch(str(param.get("locator")))
        if not match or match["path"] not in files:
            fail(f"{pid}: locator must be path#Lnn into a pinned file")
        if literal_value(param["literal"]) != param.get("value"):
            fail(f"{pid}: literal {param['literal']!r} != value {param.get('value')!r}")
    missing = REQUIRED - seen
    if missing:
        fail(f"missing parameters: {sorted(missing)}")

    v = values(payload)
    if v["dmr_frame_bytes"] * 8 != v["dmr_frame_bits"]:
        fail("DMR frame bits must equal frame bytes x 8")
    if v["dmr_voice_payload_bits"] + v["dmr_sync_bits"] != v["dmr_frame_bits"]:
        fail("DMR voice payload + sync bits must equal the frame bits")
    if v["dmr_voice_payload_bits"] % v["dmr_ambe_frames_per_burst"]:
        fail("DMR voice payload must divide evenly into the AMBE blocks")
    mask = v["dmr_sync_mask"]
    mask_bits = sum(bin(b).count("1") for b in mask)
    if mask_bits != v["dmr_sync_bits"]:
        fail("DMR sync mask must cover exactly the sync length")
    for pid in DMR_SYNCS:
        pattern = v[pid]
        if len(pattern) != len(mask) or any(b & ~m & 0xFF for b, m in zip(pattern, mask)):
            fail(f"{pid}: sync pattern must fit the sync mask")
    if len({sync_hex(v[pid]) for pid in DMR_SYNCS}) != len(DMR_SYNCS):
        fail("DMR sync patterns must be distinct")
    if v["dstar_voice_bytes"] + v["dstar_slow_data_bytes"] != v["dstar_frame_bytes"]:
        fail("D-STAR voice + slow data bytes must equal the frame bytes")
    if len(v["ysf_sync"]) != v["ysf_sync_bytes"]:
        fail("YSF sync array length must equal the declared sync length")
    if not payload.get("not_stated_by_source"):
        fail("not_stated_by_source must list what the source does not establish")


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
    for param in payload["parameters"]:
        match = LOCATOR_RE.fullmatch(param["locator"])
        line = (clone / match["path"]).read_text(encoding="utf-8").splitlines()[int(match["start"]) - 1]
        if param["token"] not in line or param["literal"] not in line.split(param["token"], 1)[1]:
            fail(f"{param['id']}: token/literal not found at {param['locator']}")


def load() -> tuple[dict, dict]:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in json.loads(SOURCES.read_text(encoding="utf-8"))["sources"]}
    return payload, sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--verify-clone", type=Path, help="local clone of the pinned repository")
    args = parser.parse_args(argv)
    payload, sources = load()
    try:
        validate(payload, sources)
        if args.verify_clone:
            verify_clone(payload, args.verify_clone)
    except DigitalVoiceError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    extra = " and matched the pinned clone" if args.verify_clone else ""
    print(f"PASS: validated {len(payload['parameters'])} DMR/D-STAR/YSF parameter(s) (community tier, commit-pinned){extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
