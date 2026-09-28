#!/usr/bin/env python3
"""Source-grounded Q-code and RS(T) training helpers."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Q_CODES = ROOT / "data" / "q_codes.json"
RST = ROOT / "data" / "rst_reports.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def lookup_qcode(code: str, payload: dict | None = None) -> dict:
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Q-code must be a non-empty string")
    normalized = code.strip().upper()
    data = payload or _load(Q_CODES)
    by_code = {item["code"]: item for item in data["codes"]}
    if normalized not in by_code:
        raise ValueError(f"unsupported Q-code: {normalized}")
    result = dict(by_code[normalized])
    result["source_ids"] = list(data["source_ids"])
    result["legal_verdict"] = None
    return result


def generate_qcode_prompt(seed: int = 0, payload: dict | None = None) -> dict:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    data = payload or _load(Q_CODES)
    rng = random.Random(seed)
    item = dict(rng.choice(data["codes"]))
    form = rng.choice(("question", "statement"))
    return {
        "code": item["code"],
        "form": form,
        "answer": item[f"{form}_summary"],
        "source_ids": list(data["source_ids"]),
        "legal_verdict": None,
    }


def parse_rst(report: str, mode: str, payload: dict | None = None) -> dict:
    if not isinstance(report, str) or not report.strip():
        raise ValueError("report must be a non-empty string")
    if mode not in {"phone", "cw"}:
        raise ValueError("mode must be 'phone' or 'cw'")
    value = report.strip()
    expected_length = 2 if mode == "phone" else 3
    if len(value) != expected_length or not value.isdigit():
        raise ValueError(f"{mode} report must be exactly {expected_length} digits")

    r, s = value[0], value[1]
    t = value[2] if mode == "cw" else None
    data = payload or _load(RST)

    if r not in data["readability"] or s not in data["strength"]:
        raise ValueError("RST readability/strength digit is outside the supported range")
    if t is not None and t not in data["tone"]:
        raise ValueError("RST tone digit is outside the supported range")

    return {
        "report": value,
        "mode": mode,
        "readability": {"value": int(r), "summary": data["readability"][r]},
        "strength": {"value": int(s), "summary": data["strength"][s]},
        "tone": None if t is None else {"value": int(t), "summary": data["tone"][t]},
        "source_ids": list(data["source_ids"]),
        "legal_verdict": None,
    }


def generate_rst_prompt(
    mode: str = "phone",
    seed: int = 0,
    payload: dict | None = None,
) -> dict:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if mode not in {"phone", "cw"}:
        raise ValueError("mode must be 'phone' or 'cw'")

    rng = random.Random(seed)
    report = f"{rng.randint(1, 5)}{rng.randint(1, 9)}"
    if mode == "cw":
        report += str(rng.randint(1, 9))
    return parse_rst(report, mode, payload)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Source-grounded Q-code and RS(T) trainer; no transmit/legal verdicts."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    qcode = sub.add_parser("qcode", help="Look up a supported amateur Q-code")
    qcode.add_argument("code")

    qquiz = sub.add_parser("qquiz", help="Generate a deterministic Q-code flashcard")
    qquiz.add_argument("--seed", type=int, default=0)

    rst = sub.add_parser("rst", help="Interpret a numeric RS or RST report")
    rst.add_argument("report")
    rst.add_argument("--mode", choices=("phone", "cw"), required=True)

    rstquiz = sub.add_parser("rstquiz", help="Generate a deterministic RS(T) practice report")
    rstquiz.add_argument("--mode", choices=("phone", "cw"), default="phone")
    rstquiz.add_argument("--seed", type=int, default=0)

    args = parser.parse_args()
    if args.command == "qcode":
        result = lookup_qcode(args.code)
    elif args.command == "qquiz":
        result = generate_qcode_prompt(args.seed)
    elif args.command == "rst":
        result = parse_rst(args.report, args.mode)
    else:
        result = generate_rst_prompt(args.mode, args.seed)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
