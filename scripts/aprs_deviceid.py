#!/usr/bin/env python3
"""APRS device identification (tocall) lookup and validator.

``data/aprs_deviceid.json`` is a CC BY-SA 2.0 adaptation of
``tocalls.yaml`` from the APRS device identification database
(aprsorg/aprs-deviceid), pinned to an exact commit. Adaptation: YAML to
JSON; the class, tocall and Mic-E (new-style ``mice`` and Kenwood
``micelegacy``) indexes; per-person ``contact`` fields omitted; a
``path#Lnn`` locator added to every entry.

Lookup follows the source README's algorithm: an exact match against
non-wildcard tocalls first, then the wildcard entry with the longest
match (``?`` = any character, lower-case ``n`` = digit, ``*`` = any rest).
When two wildcard entries match equally well the result is ambiguous and
no single device is claimed. Mic-E codes are matched exactly (new-style
2-character comment suffix, or legacy 1-character prefix with optional
1-character suffix); every exact match is returned.

Usage::

    python scripts/aprs_deviceid.py                 # validate
    python scripts/aprs_deviceid.py APDW16          # look up a tocall
    python scripts/aprs_deviceid.py --mice "_3"     # look up a Mic-E code
    python scripts/aprs_deviceid.py --verify-clone /path/to/aprs-deviceid
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
DATA = ROOT / "data" / "aprs_deviceid.json"
SOURCES = ROOT / "data" / "sources.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PATTERN_RE = re.compile(r"^[A-Z0-9][A-Z0-9?n]{1,5}\*?$")
TOCALL_RE = re.compile(r"^[A-Z0-9]{1,6}$")
LOCATOR_RE = re.compile(r"^(?P<path>[\w./-]+)#L(?P<start>\d+)(?:-L(?P<end>\d+))?$")
KEPT_FIELDS = ("vendor", "model", "class", "os", "features")
WILDCARDS = frozenset("?n*")


class AprsDeviceIdError(ValueError):
    pass


def fail(message: str) -> None:
    raise AprsDeviceIdError(message)


def is_wildcard(pattern: str) -> bool:
    return any(ch in WILDCARDS for ch in pattern)


def pattern_regex(pattern: str) -> re.Pattern:
    parts = []
    for ch in pattern:
        parts.append({"?": "[A-Z0-9]", "n": "[0-9]", "*": "[A-Z0-9]*"}.get(ch, re.escape(ch)))
    return re.compile("".join(parts))


def literal_length(pattern: str) -> int:
    return sum(ch not in WILDCARDS for ch in pattern)


def normalize_tocall(value: str) -> str:
    """Upper-case and drop an AX.25 SSID (``APDW16-1`` -> ``APDW16``)."""
    base = value.strip().upper().split("-", 1)[0]
    if not TOCALL_RE.fullmatch(base):
        raise ValueError(f"not an APRS destination callsign: {value!r}")
    return base


def lookup(tocall: str, payload: dict) -> dict:
    """Return ``{"status", "tocall", "matches"}``.

    status: ``exact`` | ``wildcard`` | ``ambiguous`` | ``not_found``.
    """
    base = normalize_tocall(tocall)
    entries = payload["tocalls"]
    exact = [e for e in entries if not is_wildcard(e["tocall"]) and e["tocall"] == base]
    if exact:
        return {"status": "exact", "tocall": base, "matches": exact}
    hits = [e for e in entries if is_wildcard(e["tocall"]) and pattern_regex(e["tocall"]).fullmatch(base)]
    if not hits:
        return {"status": "not_found", "tocall": base, "matches": []}
    best = max(literal_length(e["tocall"]) for e in hits)
    top = [e for e in hits if literal_length(e["tocall"]) == best]
    return {"status": "wildcard" if len(top) == 1 else "ambiguous", "tocall": base, "matches": top}


def lookup_mice(code: str, payload: dict) -> dict:
    """Exact Mic-E device match. status: ``found`` | ``not_found``.

    A 2-character code is compared with new-style suffixes and with legacy
    prefix+suffix pairs; a 1-character code with legacy prefix-only entries.
    """
    if not 1 <= len(code) <= 2:
        raise ValueError(f"Mic-E device code must be 1 or 2 characters: {code!r}")
    matches = [dict(e, kind="mice") for e in payload["mice"] if e["suffix"] == code]
    for entry in payload["micelegacy"]:
        if entry["prefix"] + entry.get("suffix", "") == code:
            matches.append(dict(entry, kind="micelegacy"))
    return {"status": "found" if matches else "not_found", "code": code, "matches": matches}


def _section_item_lines(yaml_lines: list[str], section: str) -> list[int]:
    """Line numbers of the list items of one top-level YAML section, in order."""
    numbers, inside, indent = [], False, None
    for number, line in enumerate(yaml_lines, start=1):
        if re.match(r"^[A-Za-z_]+:", line):
            inside = line.startswith(f"{section}:")
            continue
        item = re.match(r"^(\s*)-\s", line) if inside else None
        if item:
            indent = len(item.group(1)) if indent is None else indent
            if len(item.group(1)) == indent:
                numbers.append(number)
    return numbers


def _keep(item: dict, keys: tuple[str, ...]) -> dict:
    return {k: item[k] for k in keys if k in item}


def extract(document: dict, yaml_lines: list[str], source_path: str) -> dict:
    """Build the adapted classes/tocalls/Mic-E indexes from the parsed source YAML."""
    line_of = {}
    for number, line in enumerate(yaml_lines, start=1):
        match = re.match(r"^\s*-\s*tocall:\s*\"?([^\"\s]+)\"?\s*$", line)
        if match:
            line_of.setdefault(match.group(1), number)
    tocalls = []
    for item in document["tocalls"]:
        entry = {"tocall": item["tocall"]}
        for field in KEPT_FIELDS:
            if field in item:
                entry[field] = item[field]
        entry["locator"] = f"{source_path}#L{line_of[item['tocall']]}"
        tocalls.append(entry)
    classes = [{"class": c["class"], "shown": c["shown"], "description": c["description"]}
               for c in document["classes"]]
    result = {"classes": classes, "tocalls": tocalls}
    for section, keys in (("mice", ("suffix",)), ("micelegacy", ("prefix", "suffix"))):
        lines = _section_item_lines(yaml_lines, section)
        if len(lines) != len(document[section]):
            raise AprsDeviceIdError(f"cannot locate every {section} entry in {source_path}")
        result[section] = [dict(_keep(item, keys + KEPT_FIELDS), locator=f"{source_path}#L{line}")
                           for item, line in zip(document[section], lines)]
    return result


def validate(payload: dict, sources: dict) -> None:
    if payload.get("schema_version") != 1:
        fail("schema_version must be 1")
    source = sources.get(payload.get("source_id"))
    if source is None:
        fail("source_id is not registered in data/sources.json")
    if source["verification_status"] != "verified":
        fail("source provenance must be verified")
    if source["legal_status"] != "not_applicable" or source["source_type"] == "official_legal":
        fail("the APRS device registry must not be a legal source")

    lic = payload.get("license") or {}
    if lic.get("id") != "CC-BY-SA-2.0" or not str(lic.get("url", "")).startswith("https://creativecommons.org/licenses/by-sa/2.0"):
        fail("license must be CC-BY-SA-2.0 with its canonical URL")
    for key in ("attribution", "adaptation"):
        if not isinstance(lic.get(key), str) or not lic[key].strip():
            fail(f"license.{key} is required (CC BY-SA attribution and change notice)")

    prov = payload.get("provenance") or {}
    if not str(prov.get("repository", "")).startswith("https://github.com/"):
        fail("provenance.repository must be an https GitHub URL")
    if not HEX40.fullmatch(str(prov.get("commit", ""))):
        fail("provenance.commit must be a 40-hex commit SHA")
    if prov["commit"] not in source.get("url", ""):
        fail("source url must pin the same commit")
    files = {f.get("path"): f for f in prov.get("files", [])}
    if "tocalls.yaml" not in files:
        fail("provenance.files must include tocalls.yaml")
    for path, item in files.items():
        if not HEX40.fullmatch(str(item.get("git_blob_sha1", ""))):
            fail(f"{path}: git_blob_sha1 must be 40-hex")
        if not HEX64.fullmatch(str(item.get("sha256", ""))):
            fail(f"{path}: sha256 must be 64-hex")

    def check_locator(locator: object, owner: str) -> None:
        match = LOCATOR_RE.fullmatch(str(locator))
        if not match or match["path"] not in files:
            fail(f"{owner}: locator must be path#Lnn into a pinned file")

    check_locator(payload.get("lookup_algorithm_locator"), "lookup_algorithm_locator")
    if "contact" not in payload.get("omitted_fields", []):
        fail("omitted_fields must record that personal contact fields are dropped")

    classes = {c.get("class") for c in payload.get("classes", [])}
    if not classes or None in classes:
        fail("classes index is required")
    seen = set()
    for entry in payload.get("tocalls", []):
        pattern = entry.get("tocall")
        if not isinstance(pattern, str) or not PATTERN_RE.fullmatch(pattern):
            fail(f"invalid tocall pattern {pattern!r}")
        if pattern in seen:
            fail(f"duplicate tocall {pattern}")
        seen.add(pattern)
        if "contact" in entry:
            fail(f"{pattern}: contact fields must not be copied")
        extra = set(entry) - {"tocall", "locator", *KEPT_FIELDS}
        if extra:
            fail(f"{pattern}: unexpected fields {sorted(extra)}")
        if "class" in entry and entry["class"] not in classes:
            fail(f"{pattern}: class {entry['class']} is not in the classes index")
        if not entry.get("vendor") and not entry.get("model"):
            fail(f"{pattern}: vendor or model is required")
        check_locator(entry.get("locator"), pattern)
    if len(seen) < 100:
        fail("tocall index looks truncated")

    codes = set()
    for section, shape in (("mice", {"suffix": 2}), ("micelegacy", {"prefix": 1, "suffix": 1})):
        entries = payload.get(section)
        if not entries:
            fail(f"{section} index is required")
        for entry in entries:
            owner = f"{section}:{entry.get('prefix', '')}{entry.get('suffix', '')}"
            for key, length in shape.items():
                value = entry.get(key)
                required = section == "mice" or key == "prefix"
                if (value is None and required) or (value is not None and (not isinstance(value, str) or len(value) != length)):
                    fail(f"{owner}: {key} must be a {length}-character string")
            if "contact" in entry:
                fail(f"{owner}: contact fields must not be copied")
            extra = set(entry) - {"locator", *shape, *KEPT_FIELDS}
            if extra:
                fail(f"{owner}: unexpected fields {sorted(extra)}")
            if "class" in entry and entry["class"] not in classes:
                fail(f"{owner}: class {entry['class']} is not in the classes index")
            if not entry.get("vendor") or not entry.get("model"):
                fail(f"{owner}: vendor and model are required")
            key = (section, entry.get("prefix"), entry.get("suffix"))
            if key in codes:
                fail(f"duplicate {owner}")
            codes.add(key)
            check_locator(entry.get("locator"), owner)


def verify_clone(payload: dict, clone: Path) -> None:
    """Re-derive the adaptation from a clone at the pinned commit."""
    import yaml  # optional dependency, only needed for clone verification

    head = subprocess.run(["git", "-C", str(clone), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    if head != payload["provenance"]["commit"]:
        fail(f"clone HEAD {head} != pinned commit")
    for item in payload["provenance"]["files"]:
        data = (clone / item["path"]).read_bytes()
        blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        if blob != item["git_blob_sha1"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            fail(f"{item['path']}: file hash differs from pinned provenance")
    text = (clone / "tocalls.yaml").read_text(encoding="utf-8")
    rebuilt = extract(yaml.safe_load(text), text.splitlines(), "tocalls.yaml")
    if any(rebuilt[k] != payload[k] for k in ("classes", "tocalls", "mice", "micelegacy")):
        fail("adapted indexes differ from a fresh extraction of the pinned tocalls.yaml")
    readme = (clone / "README.md").read_text(encoding="utf-8").splitlines()
    match = LOCATOR_RE.fullmatch(payload["lookup_algorithm_locator"])
    cited = "\n".join(readme[int(match["start"]) - 1:int(match["end"] or match["start"])])
    if "longest match" not in cited or "exact match" not in cited:
        fail("lookup_algorithm_locator does not cite the README lookup algorithm")


def load() -> tuple[dict, dict]:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in json.loads(SOURCES.read_text(encoding="utf-8"))["sources"]}
    return payload, sources


def describe(entry: dict, classes: dict) -> str:
    who = " ".join(x for x in (entry.get("vendor"), entry.get("model")) if x) or "?"
    extra = [classes.get(entry["class"], entry["class"])] if entry.get("class") else []
    if entry.get("os"):
        extra.append(entry["os"])
    return f"{entry['tocall']} → {who}" + (f" ({', '.join(extra)})" if extra else "")


def describe_mice(entry: dict, classes: dict) -> str:
    code = f"{entry.get('prefix', '')}{entry.get('suffix', '')}"
    label = "Mic-E sonek" if entry["kind"] == "mice" else "Mic-E (eski Kenwood) önek/sonek"
    extra = [classes.get(entry["class"], entry["class"])] if entry.get("class") else []
    if "messaging" in entry.get("features", []):
        extra.append("mesajlaşma")
    return f"{label} \"{code}\" → {entry['vendor']} {entry['model']}" + (f" ({', '.join(extra)})" if extra else "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("tocall", nargs="?", help="APRS destination callsign to look up")
    parser.add_argument("--mice", help="Mic-E device code (1-2 characters) to look up")
    parser.add_argument("--verify-clone", type=Path, help="local clone of the pinned repository")
    args = parser.parse_args(argv)
    payload, sources = load()
    try:
        validate(payload, sources)
        if args.verify_clone:
            verify_clone(payload, args.verify_clone)
    except AprsDeviceIdError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.mice is not None:
        classes = {c["class"]: c["shown"] for c in payload["classes"]}
        result = lookup_mice(args.mice, payload)
        print(f"{result['code']!r}: {result['status']}")
        for entry in result["matches"]:
            print(f"- {describe_mice(entry, classes)} [{entry['locator']}]")
        return 0
    if args.tocall:
        classes = {c["class"]: c["shown"] for c in payload["classes"]}
        result = lookup(args.tocall, payload)
        print(f"{result['tocall']}: {result['status']}")
        for entry in result["matches"]:
            print(f"- {describe(entry, classes)} [{entry['locator']}]")
        return 0
    extra = " and matched the pinned clone" if args.verify_clone else ""
    print(f"PASS: validated {len(payload['tocalls'])} APRS tocall + {len(payload['mice']) + len(payload['micelegacy'])} Mic-E entries (CC BY-SA 2.0, commit-pinned){extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
