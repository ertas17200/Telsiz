#!/usr/bin/env python3
"""Deterministic helper for the emergency communications source layer."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "emergency_comms.json"


def load_registry() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _by_id(items: list[dict]) -> dict[str, dict]:
    return {item["id"]: item for item in items}


def answer_topic(question: str, registry: dict | None = None) -> dict:
    registry = registry or load_registry()
    q = question.casefold()
    official = _by_id(registry["official_context"])
    practice = _by_id(registry["operating_practice"])

    short: list[str] = []
    source_ids: list[str] = []

    def add_source(source_id: str) -> None:
        if source_id not in source_ids:
            source_ids.append(source_id)

    if "tamp" in q:
        short.append(official["TR.TAMP.PURPOSE"]["claim_tr"])
        short.append(official["TR.TAMP.SCOPE"]["claim_tr"])
        add_source("TR.AFAD.TAMP.2022")

    levels = [level.upper() for level in re.findall(r"(?<![a-z0-9])(s[1-4])(?![a-z0-9])", q)]
    if levels:
        short.append(official["TR.TAMP.RESPONSE_LEVELS"]["claim_tr"])
        add_source("TR.AFAD.TAMP.2022")

    if any(token in q for token in ("frekans", "kanal", "mhz", "khz")):
        short.append(
            "Bu acil durum katmanı Türkiye için tek/genel bir afet frekansı veya kanal yetkisi tanımlamaz; "
            "buradan yayın izni ya da frekans yetkisi çıkarılmaz."
        )
        add_source("TR.AFAD.TAMP.2022")
        add_source("IARU.R1.EMCOMM.PROCEDURES")

    if any(token in q for token in ("görev", "gorev", "yetki", "gönüll", "gonull", "resmî", "resmi")):
        short.append(
            "Amatör telsizci olmak tek başına TAMP kapsamında resmî görevlendirme veya ek yayın yetkisi kanıtı değildir; "
            "resmî görev/yetki ayrıca yetkili kaynak ve görevlendirme üzerinden doğrulanmalıdır."
        )
        add_source("TR.AFAD.TAMP.2022")

    if not short or any(token in q for token in ("mesaj", "haberleş", "haberles", "acil", "afet", "emergency")):
        short.append(practice["IARU.EMCOMM.TRAINING_PURPOSE"]["claim_tr"])
        short.append(practice["IARU.EMCOMM.ACCURACY"]["claim_tr"])
        short.append(practice["IARU.EMCOMM.COMMON_FORMAT"]["claim_tr"])
        add_source("IARU.R1.EMCOMM.PROCEDURES")

    return {
        "short": short,
        "source_ids": source_ids,
        "legal_permission_from_this_layer": registry["authority_contract"]["legal_permission_from_this_layer"],
        "frequency_inference": registry["authority_contract"]["frequency_inference"],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("question")
    args = p.parse_args()
    result = answer_topic(args.question)
    for line in result["short"]:
        print(f"- {line}")
    print(f"LEGAL_PERMISSION={result['legal_permission_from_this_layer']}")
    print(f"FREQUENCY_INFERENCE={result['frequency_inference']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
