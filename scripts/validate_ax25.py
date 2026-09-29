#!/usr/bin/env python3
"""Validate data/ax25_parameters.json (AX.25 / HDLC / 1200 baud AFSK).

The file records factual protocol parameters observed in an independent
open-source TNC (Dire Wolf), pinned to an exact commit. No source code is
copied. Every parameter carries a ``path#Lnn`` locator, the identifier
(``token``) found on that line and the literal written after it (or the
literal itself when it is the token, as for an FCS table entry).

Checks without a clone: provenance format, community tier, numeric
literal == stored value, address arithmetic (min + repeaters == max),
tone pair ordering, and that the reflected FCS polynomial is the bit
reversal of the CCITT polynomial x^16 + x^12 + x^5 + 1.

``--verify-clone PATH`` re-checks file hashes, every token/literal at its
locator, and regenerates the 256-entry FCS table from the polynomial and
compares it with the table in the pinned source.
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
DATA = ROOT / "data" / "ax25_parameters.json"
SOURCES = ROOT / "data" / "sources.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
LOCATOR_RE = re.compile(r"^(?P<path>[\w./-]+)#L(?P<start>\d+)(?:-L(?P<end>\d+))?$")
CCITT_POLY = 0x1021  # x^16 + x^12 + x^5 + 1 (normal form)
REQUIRED = {
    "hdlc_flag", "bit_stuffing_run", "bit_order", "line_coding", "fcs_init", "fcs_final_xor",
    "fcs_polynomial_reflected", "fcs_byte_order", "address_field_bytes", "min_addresses",
    "max_repeaters", "max_addresses", "ui_frame_control", "aprs_pid",
    "afsk1200_mark_hz", "afsk1200_space_hz", "afsk1200_baud",
}
TOPICS = {"hdlc", "fcs", "ax25", "afsk"}
SCOPES = {"implementation_limit", "implementation_default"}


class Ax25Error(ValueError):
    pass


def fail(message: str) -> None:
    raise Ax25Error(message)


def reflect16(value: int) -> int:
    return int(f"{value:016b}"[::-1], 2)


def fcs_table(poly_reflected: int) -> list[int]:
    table = []
    for byte in range(256):
        crc = byte
        for _ in range(8):
            crc = (crc >> 1) ^ poly_reflected if crc & 1 else crc >> 1
        table.append(crc)
    return table


def fcs(data: bytes, params: dict) -> int:
    """FCS computed only from the recorded parameters (used by tests/answers)."""
    table = fcs_table(params["fcs_polynomial_reflected"])
    crc = params["fcs_init"]
    for byte in data:
        crc = (crc >> 8) ^ table[(crc ^ byte) & 0xFF]
    return crc ^ params["fcs_final_xor"]


def values(payload: dict) -> dict:
    return {p["id"]: p["value"] for p in payload["parameters"]}


def derived(v: dict) -> dict:
    return {
        "afsk_shift_hz": v["afsk1200_space_hz"] - v["afsk1200_mark_hz"],
        "bit_time_us": 1_000_000 / v["afsk1200_baud"],
        "max_address_field_bytes": v["max_addresses"] * v["address_field_bytes"],
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

    def check_locator(locator: object, owner: str) -> None:
        match = LOCATOR_RE.fullmatch(str(locator))
        if not match or match["path"] not in files:
            fail(f"{owner}: locator must be path#Lnn into a pinned file")

    check_locator(payload.get("fcs_table_locator"), "fcs_table_locator")
    seen = set()
    for param in payload.get("parameters", []):
        pid = param.get("id")
        if pid in seen:
            fail(f"duplicate parameter {pid}")
        seen.add(pid)
        if param.get("topic") not in TOPICS:
            fail(f"{pid}: topic must be one of {sorted(TOPICS)}")
        if "scope" in param and param["scope"] not in SCOPES:
            fail(f"{pid}: scope must be one of {sorted(SCOPES)}")
        for key in ("meaning", "token", "literal"):
            if not isinstance(param.get(key), str) or not param[key].strip():
                fail(f"{pid}: {key} is required")
        check_locator(param.get("locator"), pid)
        value = param.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            fail(f"{pid}: value must be an integer or a string")
        try:
            literal_value = int(param["literal"], 0)
        except ValueError:
            literal_value = None
        if isinstance(value, int) and literal_value is not None and literal_value != value:
            fail(f"{pid}: literal {param['literal']} != value {value}")
    missing = REQUIRED - seen
    if missing:
        fail(f"missing parameters: {sorted(missing)}")

    v = values(payload)
    if v["min_addresses"] + v["max_repeaters"] != v["max_addresses"]:
        fail("min_addresses + max_repeaters must equal max_addresses")
    if reflect16(CCITT_POLY) != v["fcs_polynomial_reflected"]:
        fail("fcs_polynomial_reflected must be the bit reversal of the CCITT polynomial 0x1021")
    if not 0 < v["afsk1200_mark_hz"] < v["afsk1200_space_hz"]:
        fail("AFSK mark tone must be below the space tone")
    if v["hdlc_flag"] != 0x7E:
        fail("HDLC flag must be 0x7E")
    if not payload.get("not_stated_by_source"):
        fail("not_stated_by_source must list what the source does not establish")


def _cited(clone: Path, locator: str) -> str:
    match = LOCATOR_RE.fullmatch(locator)
    lines = (clone / match["path"]).read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[int(match["start"]) - 1:int(match["end"] or match["start"])])


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
        text = _cited(clone, param["locator"])
        if param["token"] not in text:
            fail(f"{param['id']}: token '{param['token']}' not found at {param['locator']}")
        if param["literal"] != param["token"] and param["literal"] not in text.split(param["token"], 1)[1]:
            fail(f"{param['id']}: literal '{param['literal']}' does not follow the token at {param['locator']}")
    table = [int(x, 16) for x in re.findall(r"0x[0-9a-fA-F]{4}", _cited(clone, payload["fcs_table_locator"]))]
    if table != fcs_table(values(payload)["fcs_polynomial_reflected"]):
        fail("FCS table in the pinned source differs from the table generated from the polynomial")


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
    except Ax25Error as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    extra = " and matched the pinned clone (incl. FCS table)" if args.verify_clone else ""
    print(f"PASS: validated {len(payload['parameters'])} AX.25/HDLC/AFSK parameter(s) (community tier, commit-pinned){extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
