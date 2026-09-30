#!/usr/bin/env python3
"""Man-made and galactic radio noise (Fa) from the ITU-R SG3 P372 code.

``data/radio_noise.json`` records the coefficients of Fa = c - d*log10(f)
(f in MHz) for the man-made noise categories and for galactic noise, as
written in the ITU-R Study Group 3 reference software (ITURHFProp/P372),
pinned to an exact commit, with ``path#Lnn`` locators.

Fail-closed rules:
- a frequency outside the source's documented 1.6-30 MHz input range is
  rejected (no extrapolation);
- categories the source marks as not in P.372-10 (QUIET, NOISY) and
  atmospheric noise (needs location/month/time coefficients) are absent;
- the answer never calls this a measurement or a legal limit.

Usage::

    python scripts/radio_noise.py                  # validate
    python scripts/radio_noise.py 7.1              # Fa for every category at 7.1 MHz
    python scripts/radio_noise.py --verify-clone /path/to/ITU-R-HF
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "radio_noise.json"
SOURCES = ROOT / "data" / "sources.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
LOCATOR_RE = re.compile(r"^(?P<path>[\w./-]+)#L(?P<start>\d+)(?:-L(?P<end>\d+))?$")
COEFS = ("c", "d", "upper_decile_db", "lower_decile_db")
CATEGORIES = ("CITY", "RESIDENTIAL", "RURAL", "QUIETRURAL")


class RadioNoiseError(ValueError):
    pass


def fail(message: str) -> None:
    raise RadioNoiseError(message)


def fa(entry: dict, frequency_mhz: float) -> float:
    return entry["c"]["value"] - entry["d"]["value"] * math.log10(frequency_mhz)


def evaluate(frequency_mhz: float, payload: dict) -> dict:
    """Fa (dB) per man-made category and for galactic noise at one frequency."""
    formula = payload["formula"]
    if not formula["frequency_min_mhz"] <= frequency_mhz <= formula["frequency_max_mhz"]:
        raise ValueError(
            f"{frequency_mhz:g} MHz is outside the source input range "
            f"{formula['frequency_min_mhz']:g}-{formula['frequency_max_mhz']:g} MHz")
    return {
        "frequency_mhz": frequency_mhz,
        "man_made": [{"id": e["id"], "name_tr": e["name_tr"], "fa_db": fa(e, frequency_mhz),
                      "upper_decile_db": e["upper_decile_db"]["value"],
                      "lower_decile_db": e["lower_decile_db"]["value"]} for e in payload["man_made"]],
        "galactic_fa_db": fa(payload["galactic"], frequency_mhz),
    }


def _iter_coefficients(payload: dict):
    for entry in payload["man_made"]:
        for key in COEFS:
            yield f"{entry['id']}.{key}", entry[key]
    for key in COEFS:
        yield f"galactic.{key}", payload["galactic"][key]


def validate(payload: dict, sources: dict) -> None:
    if payload.get("schema_version") != 1:
        fail("schema_version must be 1")
    source = sources.get(payload.get("source_id"))
    if source is None:
        fail("source_id is not registered in data/sources.json")
    if source["verification_status"] != "verified":
        fail("source provenance must be verified")
    if source["source_type"] in {"official_legal", "official_technical"}:
        fail("authority of the reference software is pending; it must not be registered as official")
    if payload.get("trust_tier") != "reference_implementation_authority_pending" or \
            "doğrulama bekler" not in str(payload.get("trust_note", "")):
        fail("trust tier must state that authoritative corroboration is pending")

    prov = payload.get("provenance") or {}
    if not str(prov.get("repository", "")).startswith("https://github.com/"):
        fail("provenance.repository must be an https GitHub URL")
    if not HEX40.fullmatch(str(prov.get("commit", ""))):
        fail("provenance.commit must be a 40-hex commit SHA")
    if prov["commit"] not in source.get("url", ""):
        fail("source url must pin the same commit")
    files = {f.get("path"): f for f in prov.get("files", [])}
    for path, item in files.items():
        if not HEX40.fullmatch(str(item.get("git_blob_sha1", ""))) or not HEX64.fullmatch(str(item.get("sha256", ""))):
            fail(f"{path}: pinned hashes are required")

    def check_locator(locator: object, owner: str) -> None:
        match = LOCATOR_RE.fullmatch(str(locator))
        if not match or match["path"] not in files:
            fail(f"{owner}: locator must be path#Lnn into a pinned file")

    check_locator(prov.get("license_locator"), "license_locator")
    formula = payload.get("formula") or {}
    if formula.get("expression") != "Fa = c - d * log10(f)" or formula.get("frequency_unit") != "MHz":
        fail("formula must be Fa = c - d * log10(f) with f in MHz")
    for key in ("man_made_locator", "galactic_locator", "frequency_unit_and_range_locator"):
        check_locator(formula.get(key), f"formula.{key}")
    if not 0 < formula.get("frequency_min_mhz", 0) < formula.get("frequency_max_mhz", 0):
        fail("frequency range must be positive and ordered")

    ids = [e.get("id") for e in payload.get("man_made", [])]
    if tuple(ids) != CATEGORIES:
        fail(f"man_made categories must be exactly {CATEGORIES}")
    for owner, coef in _iter_coefficients(payload):
        value = coef.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            fail(f"{owner}: value must be a number")
        if coef.get("literal") != f"{value}":
            fail(f"{owner}: literal must be the value as written")
        if not coef.get("token"):
            fail(f"{owner}: token is required")
        check_locator(coef.get("locator"), owner)
    for entry in payload["man_made"]:
        if entry["d"]["value"] <= 0 or entry["upper_decile_db"]["value"] <= 0 or entry["lower_decile_db"]["value"] <= 0:
            fail(f"{entry['id']}: slope and deciles must be positive")
    # At every frequency in range: city >= residential >= rural >= quiet rural.
    for f in (formula["frequency_min_mhz"], formula["frequency_max_mhz"]):
        levels = [fa(e, f) for e in payload["man_made"]]
        if levels != sorted(levels, reverse=True):
            fail("man-made categories must be ordered from noisiest (city) to quietest (quiet rural)")
    if not payload.get("excluded") or not payload.get("not_stated_by_source"):
        fail("excluded and not_stated_by_source must be recorded")


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
    for owner, coef in _iter_coefficients(payload):
        line = _cited(clone, coef["locator"])
        if coef["token"] not in line or f"{coef['literal']};" not in line.split(coef["token"], 1)[1]:
            fail(f"{owner}: '{coef['token']} {coef['literal']};' not found at {coef['locator']}")
    formula = payload["formula"]
    if "c - d * log10(frequency)" not in _cited(clone, formula["man_made_locator"]) or \
            "c - d * log10(frequency)" not in _cited(clone, formula["galactic_locator"]):
        fail("formula lines do not match the source")
    rng = _cited(clone, formula["frequency_unit_and_range_locator"])
    if "Frequency (MHz)" not in rng or f"between {formula['frequency_min_mhz']} and {formula['frequency_max_mhz']}" not in rng:
        fail("frequency unit/range not found at its locator")
    if "free from" not in _cited(clone, payload["provenance"]["license_locator"]):
        fail("licence notice not found at its locator")


def load() -> tuple[dict, dict]:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in json.loads(SOURCES.read_text(encoding="utf-8"))["sources"]}
    return payload, sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("frequency_mhz", nargs="?", type=float)
    parser.add_argument("--verify-clone", type=Path)
    args = parser.parse_args(argv)
    payload, sources = load()
    try:
        validate(payload, sources)
        if args.verify_clone:
            verify_clone(payload, args.verify_clone)
    except RadioNoiseError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.frequency_mhz is not None:
        try:
            result = evaluate(args.frequency_mhz, payload)
        except ValueError as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 2
        for row in result["man_made"]:
            print(f"{row['id']:<12} Fa = {row['fa_db']:.1f} dB")
        print(f"{'GALACTIC':<12} Fa = {result['galactic_fa_db']:.1f} dB")
        return 0
    extra = " and matched the pinned clone" if args.verify_clone else ""
    print(f"PASS: validated {len(payload['man_made'])} man-made noise categories + galactic noise (ITU-R SG3 P372, commit-pinned){extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
