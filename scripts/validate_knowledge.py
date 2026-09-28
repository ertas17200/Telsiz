#!/usr/bin/env python3
"""Fail-closed validator for Telsiz source and rule registries.

Uses only the Python standard library so validation can run in a clean
GitHub Actions runner without installing dependencies.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources.json"
RULES = ROOT / "data" / "rules.json"
FREQUENCY_TABLE = ROOT / "data" / "frequency_table.json"
BTK_RAW_TABLE = ROOT / "data" / "btk_amateur_table_raw.json"
SOURCE_CANDIDATES = ROOT / "data" / "source_candidates.json"
SOURCE_CONFLICTS_DOC = ROOT / "docs" / "SOURCE_CONFLICTS.md"

ALLOWED_TYPES = {
    "official_legal",
    "official_technical",
    "amateur_association",
    "technical_manual",
    "educational",
    "community",
}
ALLOWED_VERIFICATION = {"verified", "pending", "unverified", "deprecated"}
ALLOWED_LEGAL_STATUS = {
    "current",
    "superseded",
    "repealed",
    "unknown",
    "not_applicable",
}
ALLOWED_RULE_TYPES = {
    "permission",
    "prohibition",
    "obligation",
    "condition",
    "definition",
    "limit",
    "guidance",
}
ALLOWED_AUTHORITIES = {"legal", "official_technical", "amateur_practice"}
ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{2,95}$")
SHA_RE = re.compile(r"^(sha256:)?[a-fA-F0-9]{64}$")
HOST_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")
CONFLICT_HEADING_RE = re.compile(r"^## (TR-[A-Z0-9-]+)\s*$", re.MULTILINE)
ALLOWED_CANDIDATE_STATUS = {"candidate_unverified", "candidate_inaccessible"}
ALLOWED_PHASES = {f"P{n}" for n in range(12)}
ALLOWED_COVERAGE = {"partial", "complete"}
ALLOWED_LICENSE_CLASSES = {"A", "B", "C"}
RESTRICTION_FIELDS = (
    "maximum_output_power",
    "emission",
    "bandwidth",
    "station_type",
    "allowed_use",
    "prohibited_use",
    "special_conditions",
    "allocation_status",
    "satellite",
    "repeater",
    "beacon",
    "emergency",
    "footnotes",
)
LIST_FIELDS = (
    "emission",
    "station_type",
    "allowed_use",
    "prohibited_use",
    "special_conditions",
    "footnotes",
)
FLAG_FIELDS = ("satellite", "repeater", "beacon", "emergency")
FREQUENCY_ROW_FIELDS = {
    "id",
    "frequency_min",
    "frequency_max",
    "unit",
    "license_class",
    "power_unit",
    "source_id",
    "source_locator",
    "verification_status",
    *RESTRICTION_FIELDS,
}
UNIT_TO_MHZ = {"kHz": 0.001, "MHz": 1.0, "GHz": 1000.0}
POWER_TO_W = {"mW": 0.001, "W": 1.0, "kW": 1000.0}
FREQ_EPSILON_MHZ = 1e-9


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def valid_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def load_json(path: Path, label: str) -> dict:
    if not path.exists():
        fail(f"missing {label}: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {label}: {exc}")
    if not isinstance(payload, dict):
        fail(f"{label} root must be an object")
    if payload.get("schema_version") != 1:
        fail(f"{label} schema_version must be 1")
    return payload


def validate_source(source: dict, index: int, seen_ids: set[str]) -> None:
    required = {
        "id",
        "title",
        "publisher",
        "source_type",
        "jurisdiction",
        "url",
        "topics",
        "verification_status",
        "verified_at",
    }
    missing = sorted(required - source.keys())
    if missing:
        fail(f"sources[{index}] missing required fields: {', '.join(missing)}")

    source_id = source["id"]
    if not isinstance(source_id, str) or not ID_RE.fullmatch(source_id):
        fail(f"sources[{index}].id is invalid: {source_id!r}")
    if source_id in seen_ids:
        fail(f"duplicate source id: {source_id}")
    seen_ids.add(source_id)

    if source["source_type"] not in ALLOWED_TYPES:
        fail(f"{source_id}: invalid source_type")

    if source["verification_status"] not in ALLOWED_VERIFICATION:
        fail(f"{source_id}: invalid verification_status")

    url = source["url"]
    if not isinstance(url, str):
        fail(f"{source_id}: url must be a string")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{source_id}: url must be absolute HTTPS")

    topics = source["topics"]
    if not isinstance(topics, list) or not topics or not all(
        isinstance(t, str) and len(t.strip()) >= 2 for t in topics
    ):
        fail(f"{source_id}: topics must be a non-empty string list")

    verified_at = source["verified_at"]
    if source["verification_status"] == "verified":
        if not isinstance(verified_at, str) or not valid_iso_datetime(verified_at):
            fail(f"{source_id}: verified source requires valid verified_at")
    elif verified_at is not None and (
        not isinstance(verified_at, str) or not valid_iso_datetime(verified_at)
    ):
        fail(f"{source_id}: invalid verified_at")

    legal_status = source.get("legal_status")
    if legal_status is not None and legal_status not in ALLOWED_LEGAL_STATUS:
        fail(f"{source_id}: invalid legal_status")

    digest = source.get("content_sha256")
    if digest is not None and (
        not isinstance(digest, str) or not SHA_RE.fullmatch(digest)
    ):
        fail(f"{source_id}: invalid content_sha256")

    if source["source_type"] == "official_legal":
        if not legal_status:
            fail(f"{source_id}: official_legal requires legal_status")
        if source["verification_status"] == "verified" and legal_status == "unknown":
            fail(f"{source_id}: verified current-use legal source cannot have unknown status")


def validate_rule(
    rule: dict,
    index: int,
    seen_ids: set[str],
    sources_by_id: dict[str, dict],
) -> None:
    required = {
        "id",
        "jurisdiction",
        "topic",
        "rule_type",
        "authority",
        "claim",
        "source_id",
        "source_locator",
        "verification_status",
        "verified_at",
        "conditions",
        "answer_tags",
    }
    missing = sorted(required - rule.keys())
    if missing:
        fail(f"rules[{index}] missing required fields: {', '.join(missing)}")

    rule_id = rule["id"]
    if not isinstance(rule_id, str) or not ID_RE.fullmatch(rule_id):
        fail(f"rules[{index}].id is invalid: {rule_id!r}")
    if rule_id in seen_ids:
        fail(f"duplicate rule id: {rule_id}")
    seen_ids.add(rule_id)

    if rule["rule_type"] not in ALLOWED_RULE_TYPES:
        fail(f"{rule_id}: invalid rule_type")
    if rule["authority"] not in ALLOWED_AUTHORITIES:
        fail(f"{rule_id}: invalid authority")
    if rule["verification_status"] not in ALLOWED_VERIFICATION:
        fail(f"{rule_id}: invalid verification_status")

    if not isinstance(rule["claim"], str) or len(rule["claim"].strip()) < 8:
        fail(f"{rule_id}: claim is too short")

    conditions = rule["conditions"]
    if not isinstance(conditions, list) or not all(
        isinstance(v, str) and len(v.strip()) >= 2 for v in conditions
    ):
        fail(f"{rule_id}: conditions must be a string list")

    tags = rule["answer_tags"]
    if not isinstance(tags, list) or not tags or not all(
        isinstance(v, str) and len(v.strip()) >= 2 for v in tags
    ):
        fail(f"{rule_id}: answer_tags must be a non-empty string list")

    locator = rule["source_locator"]
    if not isinstance(locator, dict) or not locator:
        fail(f"{rule_id}: source_locator must be a non-empty object")
    if not any(isinstance(v, str) and v.strip() for v in locator.values()):
        fail(f"{rule_id}: source_locator must contain at least one usable locator")

    verified_at = rule["verified_at"]
    if rule["verification_status"] == "verified":
        if not isinstance(verified_at, str) or not valid_iso_datetime(verified_at):
            fail(f"{rule_id}: verified rule requires valid verified_at")
    elif verified_at is not None and (
        not isinstance(verified_at, str) or not valid_iso_datetime(verified_at)
    ):
        fail(f"{rule_id}: invalid verified_at")

    source_id = rule["source_id"]
    source = sources_by_id.get(source_id)
    if source is None:
        fail(f"{rule_id}: unknown source_id {source_id}")

    if rule["verification_status"] == "verified":
        if source["verification_status"] != "verified":
            fail(f"{rule_id}: verified rule cannot cite non-verified source {source_id}")

    authority = rule["authority"]
    source_type = source["source_type"]
    if authority == "legal" and source_type != "official_legal":
        fail(f"{rule_id}: legal rule must cite official_legal source")
    if authority == "official_technical" and source_type not in {
        "official_legal",
        "official_technical",
    }:
        fail(f"{rule_id}: official_technical rule must cite an official source")
    if authority == "amateur_practice" and source_type not in {
        "amateur_association",
        "technical_manual",
        "educational",
    }:
        fail(f"{rule_id}: amateur_practice rule cites unsuitable source type")

    if (
        rule["verification_status"] == "verified"
        and authority == "legal"
        and source.get("legal_status") != "current"
    ):
        fail(f"{rule_id}: verified legal rule requires a current legal source")

    parameters = rule.get("parameters")
    if parameters is not None and not isinstance(parameters, dict):
        fail(f"{rule_id}: parameters must be an object")


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_frequency_row(row: dict, index: int, sources_by_id: dict, rules_by_id: dict) -> None:
    missing = sorted(FREQUENCY_ROW_FIELDS - row.keys())
    if missing:
        fail(f"frequency rows[{index}] missing fields: {', '.join(missing)}")
    row_id = row["id"]
    if not isinstance(row_id, str) or not ID_RE.fullmatch(row_id):
        fail(f"frequency rows[{index}].id is invalid: {row_id!r}")

    low, high = row["frequency_min"], row["frequency_max"]
    if not (_is_number(low) and _is_number(high)):
        fail(f"{row_id}: frequency bounds must be numbers")
    if not 0 < low < high:
        fail(f"{row_id}: frequency_min must be positive and below frequency_max")
    if row["unit"] not in UNIT_TO_MHZ:
        fail(f"{row_id}: invalid unit")

    classes = row["license_class"]
    if not isinstance(classes, list) or not classes or not set(classes) <= ALLOWED_LICENSE_CLASSES:
        fail(f"{row_id}: license_class must be a non-empty subset of A/B/C")

    power = row["maximum_output_power"]
    if power is not None:
        if not _is_number(power) or power <= 0:
            fail(f"{row_id}: maximum_output_power must be positive")
        if row["power_unit"] not in POWER_TO_W:
            fail(f"{row_id}: power value requires a valid power_unit")

    for field in LIST_FIELDS:
        value = row[field]
        if value is not None and (
            not isinstance(value, list)
            or not all(isinstance(v, str) and v.strip() for v in value)
        ):
            fail(f"{row_id}: {field} must be null (not extracted) or a string list")
    for field in FLAG_FIELDS:
        if row[field] is not None and not isinstance(row[field], bool):
            fail(f"{row_id}: {field} must be null (not extracted) or boolean")
    bandwidth = row["bandwidth"]
    if bandwidth is not None and not (isinstance(bandwidth, str) and bandwidth.strip()):
        fail(f"{row_id}: bandwidth must be null or a non-empty string")

    locator = row["source_locator"]
    if not isinstance(locator, dict) or not any(
        isinstance(v, str) and v.strip() for v in locator.values()
    ):
        fail(f"{row_id}: source_locator must contain a usable locator")

    if row["verification_status"] not in ALLOWED_VERIFICATION:
        fail(f"{row_id}: invalid verification_status")

    source = sources_by_id.get(row["source_id"])
    if source is None:
        fail(f"{row_id}: unknown source_id")
    if row["verification_status"] == "verified":
        if source["verification_status"] != "verified":
            fail(f"{row_id}: verified row cannot cite non-verified source")
        if source["source_type"] != "official_legal":
            fail(f"{row_id}: verified row must cite official_legal source")
        if source.get("legal_status") != "current":
            fail(f"{row_id}: verified row requires a current legal source")

    rule_id = row.get("derived_from_rule")
    if rule_id is not None:
        rule = rules_by_id.get(rule_id)
        if rule is None:
            fail(f"{row_id}: unknown derived_from_rule {rule_id}")
        params = rule.get("parameters") or {}
        # The rule states a limit over a frequency scope; a row may cover only
        # part of that scope (e.g. one visible sub-band) but never exceed it.
        row_low_mhz = low * UNIT_TO_MHZ[row["unit"]]
        row_high_mhz = high * UNIT_TO_MHZ[row["unit"]]
        if "frequency_min_mhz" in params and row_low_mhz < params["frequency_min_mhz"] - FREQ_EPSILON_MHZ:
            fail(f"{row_id}: frequency range extends below rule {rule_id} scope")
        if "frequency_max_mhz" in params and row_high_mhz > params["frequency_max_mhz"] + FREQ_EPSILON_MHZ:
            fail(f"{row_id}: frequency range extends above rule {rule_id} scope")
        row_power_w = power * POWER_TO_W[row["power_unit"]] if power is not None else None
        if "max_transmitter_output_power_w" in params and params["max_transmitter_output_power_w"] != row_power_w:
            fail(f"{row_id}: max_transmitter_output_power_w disagrees with rule {rule_id}")
        if "license_class" in params and params["license_class"] not in classes:
            fail(f"{row_id}: license_class disagrees with rule {rule_id}")
        if row["verification_status"] == "verified" and rule["verification_status"] != "verified":
            fail(f"{row_id}: verified row cannot derive from non-verified rule")


def validate_rows_within_raw(table: dict, raw: dict) -> None:
    """Every semantic row must lie inside one raw source row that lists its classes.

    Prevents a semantic row from spanning gaps between the visible source
    sub-bands (e.g. treating a 430-440 MHz power condition as an allocation).
    """
    if raw.get("source_id") != table.get("source_id"):
        fail("frequency table and raw BTK transcription cite different sources")
    raw_rows = raw.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        fail("raw BTK transcription has no rows")
    for row in table["rows"]:
        low = row["frequency_min"] * UNIT_TO_MHZ[row["unit"]]
        high = row["frequency_max"] * UNIT_TO_MHZ[row["unit"]]
        covering = [
            source_row
            for source_row in raw_rows
            if source_row.get("unit") in UNIT_TO_MHZ
            and source_row["frequency_min"] * UNIT_TO_MHZ[source_row["unit"]] <= low + FREQ_EPSILON_MHZ
            and high <= source_row["frequency_max"] * UNIT_TO_MHZ[source_row["unit"]] + FREQ_EPSILON_MHZ
        ]
        if not covering:
            fail(f"{row['id']}: range is not inside any raw BTK source row")
        if not any(set(row["license_class"]) <= set(r.get("license_classes") or []) for r in covering):
            fail(f"{row['id']}: license_class not listed for the covering raw BTK source row")


def check_row_conflicts(rows: list[dict]) -> None:
    """Reject overlapping rows for the same class that disagree on power."""
    for i, a in enumerate(rows):
        a_low = a["frequency_min"] * UNIT_TO_MHZ[a["unit"]]
        a_high = a["frequency_max"] * UNIT_TO_MHZ[a["unit"]]
        for b in rows[i + 1 :]:
            b_low = b["frequency_min"] * UNIT_TO_MHZ[b["unit"]]
            b_high = b["frequency_max"] * UNIT_TO_MHZ[b["unit"]]
            if a_low >= b_high or b_low >= a_high:
                continue
            if not set(a["license_class"]) & set(b["license_class"]):
                continue
            if a["maximum_output_power"] is None or b["maximum_output_power"] is None:
                continue
            a_w = a["maximum_output_power"] * POWER_TO_W[a["power_unit"]]
            b_w = b["maximum_output_power"] * POWER_TO_W[b["power_unit"]]
            if a_w != b_w and not (a["special_conditions"] or b["special_conditions"]):
                fail(
                    f"conflicting frequency rows {a['id']} / {b['id']}: "
                    "overlapping range and class with different power and no distinguishing condition"
                )


def validate_completeness(table: dict, source: dict) -> None:
    """Gate for coverage_status=complete (all conditions must hold)."""
    if table.get("coverage_blocker") is not None:
        fail("frequency table: complete coverage cannot carry a blocker")
    if source["verification_status"] != "verified":
        fail("frequency table: complete coverage requires a verified source")
    digest = source.get("content_sha256")
    if not digest:
        fail("frequency table: complete coverage requires source content_sha256")

    artifact = table.get("artifact")
    if not isinstance(artifact, dict):
        fail("frequency table: complete coverage requires artifact evidence")
    for key in ("source_url", "fetched_at", "http_status", "content_type", "file_size", "sha256", "pdf_page_count"):
        if artifact.get(key) in (None, ""):
            fail(f"frequency table: artifact.{key} is required for complete coverage")
    if not isinstance(artifact["sha256"], str) or not SHA_RE.fullmatch(artifact["sha256"]):
        fail("frequency table: artifact.sha256 must be a SHA-256 hex digest")
    if artifact["sha256"].removeprefix("sha256:").lower() != digest.removeprefix("sha256:").lower():
        fail("frequency table: artifact sha256 does not match source content_sha256")
    if artifact["http_status"] != 200:
        fail("frequency table: artifact http_status must be 200")

    recon = table.get("row_count_reconciliation")
    if not isinstance(recon, dict):
        fail("frequency table: complete coverage requires row_count_reconciliation")
    for key in ("table_start_locator", "table_end_locator", "source_rows_counted", "footnotes_counted", "footnotes_recorded"):
        if recon.get(key) in (None, ""):
            fail(f"frequency table: row_count_reconciliation.{key} is required")
    if recon["source_rows_counted"] != len(table["rows"]):
        fail("frequency table: source_rows_counted does not match extracted rows")
    if recon["footnotes_counted"] != recon["footnotes_recorded"]:
        fail("frequency table: footnotes_counted does not match footnotes_recorded")

    for row in table["rows"]:
        if row["verification_status"] != "verified":
            fail(f"{row['id']}: complete coverage requires every row verified")
        empty = [field for field in RESTRICTION_FIELDS if row[field] is None]
        if empty:
            fail(f"{row['id']}: complete coverage requires extracted fields: {', '.join(empty)}")


def validate_frequency_table(
    table: dict,
    sources_by_id: dict[str, dict],
    rules_by_id: dict[str, dict],
) -> None:
    coverage = table.get("coverage_status")
    if coverage not in ALLOWED_COVERAGE:
        fail("frequency table: invalid coverage_status")

    table_source = sources_by_id.get(table.get("source_id"))
    if table_source is None:
        fail("frequency table: unknown source_id")

    rows = table.get("rows")
    if not isinstance(rows, list):
        fail("frequency table: rows must be a list")

    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            fail(f"frequency rows[{index}] must be an object")
        validate_frequency_row(row, index, sources_by_id, rules_by_id)
        if row["id"] in seen:
            fail(f"duplicate frequency row id: {row['id']}")
        seen.add(row["id"])
    check_row_conflicts(rows)

    if coverage == "partial":
        blocker = table.get("coverage_blocker")
        if not isinstance(blocker, str) or len(blocker.strip()) < 8:
            fail("frequency table: partial coverage requires a coverage_blocker")
    else:
        validate_completeness(table, table_source)


def validate_source_candidates(
    payload: dict,
    sources_by_id: dict[str, dict],
    rules: list[dict],
    table: dict,
    known_conflicts: set[str],
) -> None:
    """Candidates are discovery records only; they can never ground anything."""
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        fail("source candidates: candidates must be a list")
    rule_ids = {rule["id"] for rule in rules}
    seen: set[str] = set()
    for index, cand in enumerate(candidates):
        if not isinstance(cand, dict):
            fail(f"candidates[{index}] must be an object")
        cand_id = cand.get("id")
        if not isinstance(cand_id, str) or not ID_RE.fullmatch(cand_id) or not cand_id.startswith("CAND."):
            fail(f"candidates[{index}].id must match ID pattern and start with CAND.")
        if cand_id in seen:
            fail(f"duplicate candidate id: {cand_id}")
        if cand_id in sources_by_id:
            fail(f"{cand_id}: candidate id collides with a registered source")
        seen.add(cand_id)

        for key in ("title", "publisher", "jurisdiction"):
            if not isinstance(cand.get(key), str) or len(cand[key].strip()) < 2:
                fail(f"{cand_id}: {key} is required")
        if cand.get("expected_source_type") not in ALLOWED_TYPES:
            fail(f"{cand_id}: invalid expected_source_type")
        if cand.get("status") not in ALLOWED_CANDIDATE_STATUS:
            fail(f"{cand_id}: invalid candidate status")
        if cand.get("canonical_url") is not None:
            fail(f"{cand_id}: a candidate cannot claim a canonical_url; promote it to sources.json instead")
        entry = urlparse(cand.get("search_entry_point") or "")
        if entry.scheme != "https" or not entry.netloc:
            fail(f"{cand_id}: search_entry_point must be absolute HTTPS")

        domains = cand.get("required_access_domains")
        if not isinstance(domains, list) or not domains or not all(
            isinstance(d, str) and HOST_RE.fullmatch(d) for d in domains
        ):
            fail(f"{cand_id}: required_access_domains must be a non-empty hostname list")

        unlocks = cand.get("unlocks")
        if not isinstance(unlocks, dict):
            fail(f"{cand_id}: unlocks must be an object")
        phases = unlocks.get("phases")
        if not isinstance(phases, list) or not phases or not set(phases) <= ALLOWED_PHASES:
            fail(f"{cand_id}: unlocks.phases must be a non-empty subset of P0-P11")
        if not isinstance(unlocks.get("purpose"), str) or len(unlocks["purpose"].strip()) < 8:
            fail(f"{cand_id}: unlocks.purpose is required")
        unknown_fields = set(unlocks.get("fields", [])) - set(RESTRICTION_FIELDS)
        if unknown_fields:
            fail(f"{cand_id}: unlocks unknown frequency fields {sorted(unknown_fields)}")
        unknown_conflicts = set(unlocks.get("conflicts", [])) - known_conflicts
        if unknown_conflicts:
            fail(f"{cand_id}: unlocks unknown conflicts {sorted(unknown_conflicts)}")
        unknown_rules = set(unlocks.get("rules", [])) - rule_ids
        if unknown_rules:
            fail(f"{cand_id}: unlocks unknown rules {sorted(unknown_rules)}")

        unknown_sources = set(cand.get("related_sources", [])) - set(sources_by_id)
        if unknown_sources:
            fail(f"{cand_id}: related_sources not registered {sorted(unknown_sources)}")
        cannot = cand.get("cannot_support")
        if not isinstance(cannot, list):
            fail(f"{cand_id}: cannot_support must be a list")
        if not cand["expected_source_type"].startswith("official_") and "legal_claims" not in cannot:
            fail(f"{cand_id}: non-official candidate must declare cannot_support legal_claims")

    grounded = [(rule["id"], rule["source_id"]) for rule in rules]
    grounded += [(row["id"], row["source_id"]) for row in table["rows"]]
    for item_id, source_id in grounded:
        if source_id in seen:
            fail(f"{item_id}: cites unverified candidate {source_id}")


def main() -> int:
    source_payload = load_json(SOURCES, "source registry")
    sources = source_payload.get("sources")
    if not isinstance(sources, list):
        fail("sources must be a list")

    seen_source_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            fail(f"sources[{index}] must be an object")
        validate_source(source, index, seen_source_ids)

    sources_by_id = {source["id"]: source for source in sources}

    rule_payload = load_json(RULES, "rule registry")
    rules = rule_payload.get("rules")
    if not isinstance(rules, list):
        fail("rules must be a list")

    seen_rule_ids: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            fail(f"rules[{index}] must be an object")
        validate_rule(rule, index, seen_rule_ids, sources_by_id)

    rules_by_id = {rule["id"]: rule for rule in rules}
    table = load_json(FREQUENCY_TABLE, "frequency table")
    validate_frequency_table(table, sources_by_id, rules_by_id)
    validate_rows_within_raw(table, load_json(BTK_RAW_TABLE, "raw BTK transcription"))
    known_conflicts = set(CONFLICT_HEADING_RE.findall(SOURCE_CONFLICTS_DOC.read_text(encoding="utf-8")))
    candidates = load_json(SOURCE_CANDIDATES, "source candidates")
    validate_source_candidates(candidates, sources_by_id, rules, table, known_conflicts)

    print(
        f"PASS: validated {len(sources)} source record(s), "
        f"{len(rules)} grounded rule(s), "
        f"{len(table['rows'])} frequency row(s) "
        f"and {len(candidates['candidates'])} unverified source candidate(s) "
        f"[coverage={table['coverage_status']}]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
