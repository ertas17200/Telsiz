#!/usr/bin/env python3
"""Source-grounded International Morse training helpers."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "morse_code.json"


def load_code(path: Path = DATA) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["characters"]


def encode_text(text: str, code: dict[str, str] | None = None) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    table = code or load_code()
    words = text.upper().split()
    encoded_words: list[str] = []
    for word in words:
        tokens: list[str] = []
        for char in word:
            if char not in table:
                raise ValueError(f"unsupported Morse character: {char!r}")
            tokens.append(table[char])
        encoded_words.append(" ".join(tokens))
    return " / ".join(encoded_words)


def decode_morse(value: str, code: dict[str, str] | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Morse input must be a non-empty string")
    table = code or load_code()
    reverse = {signal: char for char, signal in table.items()}
    words: list[str] = []
    for raw_word in value.strip().split("/"):
        tokens = raw_word.strip().split()
        if not tokens:
            raise ValueError("empty Morse word is not allowed")
        chars: list[str] = []
        for token in tokens:
            if token not in reverse:
                raise ValueError(f"unsupported Morse signal: {token!r}")
            chars.append(reverse[token])
        words.append("".join(chars))
    return " ".join(words)


def generate_prompt(
    length: int = 5,
    seed: int = 0,
    alphabet: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    code: dict[str, str] | None = None,
) -> dict:
    if isinstance(length, bool) or not isinstance(length, int) or not 1 <= length <= 100:
        raise ValueError("length must be an integer between 1 and 100")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    table = code or load_code()
    if not isinstance(alphabet, str) or not alphabet:
        raise ValueError("alphabet must be non-empty")
    normalized = alphabet.upper()
    unsupported = sorted(set(normalized) - set(table))
    if unsupported:
        raise ValueError(f"alphabet contains unsupported characters: {unsupported}")

    rng = random.Random(seed)
    text = "".join(rng.choice(normalized) for _ in range(length))
    return {
        "text": text,
        "morse": encode_text(text, table),
        "length": length,
        "seed": seed,
        "source_id": "ITU.R.M1677.1",
        "legal_verdict": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Source-grounded Morse training tool; no transmit/legal verdicts."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encode", help="Encode A-Z/0-9 text to Morse")
    enc.add_argument("text")

    dec = sub.add_parser("decode", help="Decode supported Morse signals")
    dec.add_argument("morse")

    quiz = sub.add_parser("quiz", help="Generate a deterministic practice prompt")
    quiz.add_argument("--length", type=int, default=5)
    quiz.add_argument("--seed", type=int, default=0)
    quiz.add_argument("--alphabet", default="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

    args = parser.parse_args()
    if args.command == "encode":
        payload = {
            "text": args.text.upper(),
            "morse": encode_text(args.text),
            "source_id": "ITU.R.M1677.1",
            "legal_verdict": None,
        }
    elif args.command == "decode":
        payload = {
            "morse": args.morse,
            "text": decode_morse(args.morse),
            "source_id": "ITU.R.M1677.1",
            "legal_verdict": None,
        }
    else:
        payload = generate_prompt(args.length, args.seed, args.alphabet)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
