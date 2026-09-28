#!/usr/bin/env python3
"""Deterministic practice-exam scorer for the Telsiz grounded question bank."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK = ROOT / "academy" / "exam_questions.json"


def load_bank(path: Path = DEFAULT_BANK) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def score_answers(bank: dict, answers: dict[str, str]) -> dict:
    if not isinstance(answers, dict):
        raise ValueError("answers must be a mapping of question_id -> option_id")

    questions = bank.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("exam bank has no questions")
    by_id = {q["id"]: q for q in questions}

    unknown_questions = sorted(set(answers) - set(by_id))
    if unknown_questions:
        raise ValueError(f"unknown question ids: {unknown_questions}")

    items = []
    correct = 0
    answered = 0
    for question in questions:
        qid = question["id"]
        selected = answers.get(qid)
        valid_options = {item["id"] for item in question["options"]}
        if selected is not None and selected not in valid_options:
            raise ValueError(f"{qid}: invalid option id {selected!r}")

        is_answered = selected is not None
        is_correct = is_answered and selected == question["correct_option_id"]
        answered += int(is_answered)
        correct += int(is_correct)
        items.append({
            "question_id": qid,
            "selected_option_id": selected,
            "correct": bool(is_correct),
            "answered": bool(is_answered),
            "source_ids": question["source_ids"],
            "rule_ids": question["rule_ids"],
        })

    total = len(questions)
    return {
        "exam_status": bank.get("exam_status"),
        "total": total,
        "answered": answered,
        "correct": correct,
        "unanswered": total - answered,
        "score_percent": round(correct * 100 / total, 2),
        "items": items,
    }


def parse_answer(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("answer must use QUESTION_ID=OPTION_ID")
    question_id, option_id = value.split("=", 1)
    if not question_id or not option_id:
        raise argparse.ArgumentTypeError("answer must use QUESTION_ID=OPTION_ID")
    return question_id, option_id


def answers_from_pairs(pairs: list[tuple[str, str]]) -> dict[str, str]:
    answers: dict[str, str] = {}
    for question_id, option_id in pairs:
        if question_id in answers:
            raise ValueError(f"duplicate answer for question {question_id}")
        answers[question_id] = option_id
    return answers


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Telsiz source-grounded practice exam scorer (not an official KEGM exam simulator)"
    )
    parser.add_argument("--list", action="store_true", help="List practice questions as JSON")
    parser.add_argument("--answer", action="append", default=[], type=parse_answer, metavar="QUESTION=OPTION")
    args = parser.parse_args()

    bank = load_bank()
    if args.list:
        print(json.dumps({
            "exam_status": bank.get("exam_status"),
            "questions": [
                {
                    "id": q["id"],
                    "prompt": q["prompt"],
                    "options": q["options"],
                    "source_ids": q["source_ids"],
                    "rule_ids": q["rule_ids"],
                }
                for q in bank["questions"]
            ],
        }, ensure_ascii=False, indent=2))
        return 0

    answers = answers_from_pairs(args.answer)
    result = score_answers(bank, answers)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
