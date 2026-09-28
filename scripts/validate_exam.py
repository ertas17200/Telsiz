#!/usr/bin/env python3
"""Fail-closed validator for the grounded practice exam bank."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "academy" / "exam_questions.json"
SOURCES = ROOT / "data" / "sources.json"
RULES = ROOT / "data" / "rules.json"
CANDIDATES = ROOT / "data" / "source_candidates.json"

QUESTION_ID_RE = re.compile(r"^EXAM\.[A-Z0-9][A-Z0-9._-]{2,95}$")
OPTION_ID_RE = re.compile(r"^[A-Z0-9]{1,4}$")
ALLOWED_STATUS = {"source_grounded", "educational_only"}
REQUIRED_FIELDS = {
    "id", "prompt", "options", "correct_option_id", "content_status",
    "legal_content", "time_sensitive", "official_exam_claim",
    "source_ids", "rule_ids", "candidate_refs", "explanation", "tags",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def load(path: Path, label: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{label}: cannot load JSON: {exc}")


def string_list(value, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        fail(f"{label} must be a string list")
    if not allow_empty and not value:
        fail(f"{label} must be non-empty")
    if len(value) != len(set(value)):
        fail(f"{label} must not contain duplicates")
    return value


def validate_bank(bank: dict, sources_payload: dict, rules_payload: dict, candidates_payload: dict) -> None:
    if bank.get("schema_version") != 1:
        fail("exam bank: schema_version must be 1")
    if bank.get("exam_status") != "practice_only":
        fail("exam bank: exam_status must remain practice_only until an official exam source is verified")

    questions = bank.get("questions")
    if not isinstance(questions, list) or not questions:
        fail("exam bank: questions must be a non-empty list")

    sources = sources_payload.get("sources")
    rules = rules_payload.get("rules")
    candidates = candidates_payload.get("candidates")
    if not isinstance(sources, list) or not isinstance(rules, list) or not isinstance(candidates, list):
        fail("exam bank: source/rule/candidate registries are malformed")

    sources_by_id = {item["id"]: item for item in sources}
    rules_by_id = {item["id"]: item for item in rules}
    candidates_by_id = {item["id"]: item for item in candidates}
    seen: set[str] = set()

    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            fail(f"exam questions[{index}] must be an object")
        missing = REQUIRED_FIELDS - set(question)
        unknown = set(question) - REQUIRED_FIELDS
        if missing:
            fail(f"exam questions[{index}] missing fields: {', '.join(sorted(missing))}")
        if unknown:
            fail(f"exam questions[{index}] unknown fields: {', '.join(sorted(unknown))}")

        qid = question["id"]
        if not isinstance(qid, str) or not QUESTION_ID_RE.fullmatch(qid):
            fail(f"exam questions[{index}].id is invalid")
        if qid in seen:
            fail(f"duplicate exam question id: {qid}")
        seen.add(qid)

        for key in ("prompt", "explanation"):
            if not isinstance(question[key], str) or len(question[key].strip()) < 8:
                fail(f"{qid}: {key} is required")
        if question["content_status"] not in ALLOWED_STATUS:
            fail(f"{qid}: invalid content_status")
        for key in ("legal_content", "time_sensitive", "official_exam_claim"):
            if not isinstance(question[key], bool):
                fail(f"{qid}: {key} must be boolean")
        if question["time_sensitive"]:
            fail(f"{qid}: time-sensitive questions require a dedicated freshness contract and are not allowed in v1")
        if question["official_exam_claim"]:
            fail(f"{qid}: official exam claim is forbidden while the canonical exam regulation/source is pending")

        options = question["options"]
        if not isinstance(options, list) or len(options) < 2:
            fail(f"{qid}: options must contain at least two choices")
        option_ids: list[str] = []
        option_texts: list[str] = []
        for opt_index, option in enumerate(options):
            if not isinstance(option, dict) or set(option) != {"id", "text"}:
                fail(f"{qid}: options[{opt_index}] must contain only id/text")
            oid, text = option["id"], option["text"]
            if not isinstance(oid, str) or not OPTION_ID_RE.fullmatch(oid):
                fail(f"{qid}: invalid option id")
            if not isinstance(text, str) or len(text.strip()) < 2:
                fail(f"{qid}: option text is required")
            option_ids.append(oid)
            option_texts.append(text.strip())
        if len(option_ids) != len(set(option_ids)):
            fail(f"{qid}: option ids must be unique")
        if len(option_texts) != len(set(option_texts)):
            fail(f"{qid}: option texts must be unique")
        if question["correct_option_id"] not in option_ids:
            fail(f"{qid}: correct_option_id must reference an option")

        source_ids = string_list(question["source_ids"], f"{qid}.source_ids")
        rule_ids = string_list(question["rule_ids"], f"{qid}.rule_ids")
        candidate_refs = string_list(question["candidate_refs"], f"{qid}.candidate_refs")
        string_list(question["tags"], f"{qid}.tags", allow_empty=False)

        unknown_sources = set(source_ids) - set(sources_by_id)
        unknown_rules = set(rule_ids) - set(rules_by_id)
        unknown_candidates = set(candidate_refs) - set(candidates_by_id)
        if unknown_sources:
            fail(f"{qid}: unknown source_ids {sorted(unknown_sources)}")
        if unknown_rules:
            fail(f"{qid}: unknown rule_ids {sorted(unknown_rules)}")
        if unknown_candidates:
            fail(f"{qid}: unknown candidate_refs {sorted(unknown_candidates)}")

        if question["content_status"] == "source_grounded":
            if candidate_refs:
                fail(f"{qid}: source_grounded question cannot cite unverified candidates")
            if not source_ids or not rule_ids:
                fail(f"{qid}: source_grounded question requires source_ids and rule_ids")
            for source_id in source_ids:
                source = sources_by_id[source_id]
                if source.get("verification_status") != "verified":
                    fail(f"{qid}: cites non-verified source {source_id}")
            for rule_id in rule_ids:
                rule = rules_by_id[rule_id]
                if rule.get("verification_status") != "verified":
                    fail(f"{qid}: cites non-verified rule {rule_id}")
                if rule.get("source_id") not in source_ids:
                    fail(f"{qid}: rule {rule_id} source must be listed in source_ids")

            if question["legal_content"]:
                for source_id in source_ids:
                    source = sources_by_id[source_id]
                    if source.get("source_type") != "official_legal":
                        fail(f"{qid}: legal question source must be official_legal")
                    if source.get("legal_status") != "current":
                        fail(f"{qid}: legal question source must be current")
                for rule_id in rule_ids:
                    if rules_by_id[rule_id].get("authority") != "legal":
                        fail(f"{qid}: legal question rule must have legal authority")
            else:
                for rule_id in rule_ids:
                    if rules_by_id[rule_id].get("authority") == "legal":
                        fail(f"{qid}: non-legal question cannot cite a legal rule")
        else:
            if question["legal_content"]:
                fail(f"{qid}: educational_only cannot contain legal content")
            if source_ids or rule_ids:
                fail(f"{qid}: educational_only cannot claim source_ids or rule_ids")
            for candidate_id in candidate_refs:
                candidate = candidates_by_id[candidate_id]
                if candidate.get("expected_source_type") != "community":
                    fail(f"{qid}: educational_only candidate reference must be community")
                cannot = candidate.get("cannot_support")
                if not isinstance(cannot, list) or "legal_claims" not in cannot:
                    fail(f"{qid}: community candidate must disclaim legal_claims")

    print(f"PASS: validated {len(questions)} grounded practice exam question(s); bank remains practice_only")


def main() -> int:
    validate_bank(
        load(BANK, "exam bank"),
        load(SOURCES, "source registry"),
        load(RULES, "rule registry"),
        load(CANDIDATES, "source candidates"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
