#!/usr/bin/env python3
"""Fail-closed validator for the Telsiz Academy manifest."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACADEMY = ROOT / "academy" / "academy.json"
SOURCES = ROOT / "data" / "sources.json"
RULES = ROOT / "data" / "rules.json"
CANDIDATES = ROOT / "data" / "source_candidates.json"

ID_RE = re.compile(r"^ACADEMY\.[A-Z0-9][A-Z0-9._-]{2,95}$")
ALLOWED_STATUS = {"source_grounded", "educational_only"}
REQUIRED_FIELDS = {
    "id",
    "title",
    "content_status",
    "legal_content",
    "legal_verdicts",
    "source_ids",
    "rule_ids",
    "candidate_refs",
    "notes",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(path: Path, label: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{label}: cannot load JSON: {exc}")


def string_list(value, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        fail(f"{label} must be a string list")
    if len(value) != len(set(value)):
        fail(f"{label} must not contain duplicates")
    return value


def validate_manifest(
    manifest: dict,
    sources_payload: dict,
    rules_payload: dict,
    candidates_payload: dict,
) -> None:
    if manifest.get("schema_version") != 1:
        fail("academy: schema_version must be 1")

    modules = manifest.get("modules")
    if not isinstance(modules, list) or not modules:
        fail("academy: modules must be a non-empty list")

    sources = sources_payload.get("sources")
    rules = rules_payload.get("rules")
    candidates = candidates_payload.get("candidates")
    if not isinstance(sources, list) or not isinstance(rules, list) or not isinstance(candidates, list):
        fail("academy: source/rule/candidate registries are malformed")

    sources_by_id = {item["id"]: item for item in sources}
    rules_by_id = {item["id"]: item for item in rules}
    candidates_by_id = {item["id"]: item for item in candidates}

    seen: set[str] = set()
    for index, module in enumerate(modules):
        if not isinstance(module, dict):
            fail(f"academy modules[{index}] must be an object")

        missing = REQUIRED_FIELDS - set(module)
        unknown = set(module) - REQUIRED_FIELDS
        if missing:
            fail(f"academy modules[{index}] missing fields: {', '.join(sorted(missing))}")
        if unknown:
            fail(f"academy modules[{index}] unknown fields: {', '.join(sorted(unknown))}")

        module_id = module["id"]
        if not isinstance(module_id, str) or not ID_RE.fullmatch(module_id):
            fail(f"academy modules[{index}].id is invalid")
        if module_id in seen:
            fail(f"duplicate academy module id: {module_id}")
        seen.add(module_id)

        if not isinstance(module["title"], str) or len(module["title"].strip()) < 3:
            fail(f"{module_id}: title is required")
        if not isinstance(module["notes"], str) or len(module["notes"].strip()) < 8:
            fail(f"{module_id}: notes are required")
        if module["content_status"] not in ALLOWED_STATUS:
            fail(f"{module_id}: invalid content_status")
        if not isinstance(module["legal_content"], bool):
            fail(f"{module_id}: legal_content must be boolean")
        if not isinstance(module["legal_verdicts"], bool):
            fail(f"{module_id}: legal_verdicts must be boolean")
        if module["legal_verdicts"]:
            fail(f"{module_id}: Academy cannot emit legal verdicts; use the decision engine")

        source_ids = string_list(module["source_ids"], f"{module_id}.source_ids")
        rule_ids = string_list(module["rule_ids"], f"{module_id}.rule_ids")
        candidate_refs = string_list(module["candidate_refs"], f"{module_id}.candidate_refs")

        unknown_sources = set(source_ids) - set(sources_by_id)
        unknown_rules = set(rule_ids) - set(rules_by_id)
        unknown_candidates = set(candidate_refs) - set(candidates_by_id)
        if unknown_sources:
            fail(f"{module_id}: unknown source_ids {sorted(unknown_sources)}")
        if unknown_rules:
            fail(f"{module_id}: unknown rule_ids {sorted(unknown_rules)}")
        if unknown_candidates:
            fail(f"{module_id}: unknown candidate_refs {sorted(unknown_candidates)}")

        if module["content_status"] == "source_grounded":
            if candidate_refs:
                fail(f"{module_id}: source_grounded module cannot cite unverified candidates")
            if not source_ids and not rule_ids:
                fail(f"{module_id}: source_grounded module needs source_ids or rule_ids")

            for source_id in source_ids:
                source = sources_by_id[source_id]
                if source.get("verification_status") != "verified":
                    fail(f"{module_id}: source_grounded module cites non-verified source {source_id}")

            for rule_id in rule_ids:
                rule = rules_by_id[rule_id]
                if rule.get("verification_status") != "verified":
                    fail(f"{module_id}: source_grounded module cites non-verified rule {rule_id}")
                if rule.get("source_id") not in source_ids:
                    fail(f"{module_id}: rule {rule_id} source must be listed in source_ids")

            if module["legal_content"]:
                if not rule_ids:
                    fail(f"{module_id}: legal_content requires at least one legal rule")
                for source_id in source_ids:
                    source = sources_by_id[source_id]
                    if source.get("source_type") != "official_legal":
                        fail(f"{module_id}: legal_content source must be official_legal")
                    if source.get("legal_status") != "current":
                        fail(f"{module_id}: legal_content source must be current")
                for rule_id in rule_ids:
                    if rules_by_id[rule_id].get("authority") != "legal":
                        fail(f"{module_id}: legal_content rule must have legal authority")
            else:
                for rule_id in rule_ids:
                    if rules_by_id[rule_id].get("authority") == "legal":
                        fail(f"{module_id}: non-legal Academy module cannot cite a legal rule")

        else:  # educational_only
            if module["legal_content"]:
                fail(f"{module_id}: educational_only cannot contain legal content")
            if source_ids or rule_ids:
                fail(f"{module_id}: educational_only cannot claim source_ids or rule_ids")
            for candidate_id in candidate_refs:
                candidate = candidates_by_id[candidate_id]
                if candidate.get("expected_source_type") != "community":
                    fail(f"{module_id}: educational_only candidate reference must be community")
                cannot = candidate.get("cannot_support")
                if not isinstance(cannot, list) or "legal_claims" not in cannot:
                    fail(f"{module_id}: community candidate must disclaim legal_claims")

    print(f"PASS: validated {len(modules)} Academy module(s); legal verdicts remain delegated to the fail-closed decision engine")


def main() -> int:
    validate_manifest(
        load(ACADEMY, "academy manifest"),
        load(SOURCES, "source registry"),
        load(RULES, "rule registry"),
        load(CANDIDATES, "source candidates"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
