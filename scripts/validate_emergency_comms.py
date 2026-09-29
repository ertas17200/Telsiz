#!/usr/bin/env python3
"""Validate emergency communications source separation and claims."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "emergency_comms.json"
SOURCES = ROOT / "data" / "sources.json"

EXPECTED_SOURCES = {"TR.AFAD.TAMP.2022", "IARU.R1.EMCOMM.PROCEDURES"}
EXPECTED_OFFICIAL = {
    "TR.TAMP.PURPOSE",
    "TR.TAMP.SCOPE",
    "TR.TAMP.PUBLICATION",
    "TR.TAMP.GROUP_COUNTS",
    "TR.TAMP.RESPONSE_LEVELS",
}
EXPECTED_PRACTICE = {
    "IARU.EMCOMM.TRAINING_PURPOSE",
    "IARU.EMCOMM.ACCURACY",
    "IARU.EMCOMM.COMMON_FORMAT",
    "IARU.EMCOMM.FRESHNESS_CAVEAT",
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"{path.name}: root must be object")
    return value


def main() -> int:
    data = load(DATA)
    sources = {s["id"]: s for s in load(SOURCES)["sources"]}

    if set(data.get("source_ids", [])) != EXPECTED_SOURCES:
        fail("source_ids mismatch")
    for source_id in EXPECTED_SOURCES:
        src = sources.get(source_id)
        if src is None or src.get("verification_status") != "verified":
            fail(f"{source_id}: verified source required")

    if sources["TR.AFAD.TAMP.2022"]["source_type"] != "official_technical":
        fail("AFAD TAMP must remain official_technical until legal text is separately grounded")
    if sources["IARU.R1.EMCOMM.PROCEDURES"]["source_type"] != "amateur_association":
        fail("IARU emergency source must remain amateur_association")

    contract = data.get("authority_contract", {})
    if contract.get("legal_permission_from_this_layer") != "PROHIBITED":
        fail("legal permission inference must be prohibited")
    if contract.get("frequency_inference") != "PROHIBITED":
        fail("frequency inference must be prohibited")
    if contract.get("amateur_status_implies_official_assignment") is not False:
        fail("amateur status must not imply official assignment")
    if contract.get("emergency_context_expands_transmit_permission") is not False:
        fail("emergency context must not expand transmit permission")

    official = data.get("official_context")
    practice = data.get("operating_practice")
    if not isinstance(official, list) or {x.get("id") for x in official} != EXPECTED_OFFICIAL:
        fail("official context set mismatch")
    if not isinstance(practice, list) or {x.get("id") for x in practice} != EXPECTED_PRACTICE:
        fail("operating practice set mismatch")

    seen: set[str] = set()
    for item in [*official, *practice]:
        item_id = item.get("id")
        if item_id in seen:
            fail(f"duplicate item id: {item_id}")
        seen.add(item_id)
        if item.get("legal_rule") is not False:
            fail(f"{item_id}: this layer may not contain legal rules")
        if not isinstance(item.get("claim_tr"), str) or len(item["claim_tr"]) < 30:
            fail(f"{item_id}: claim_tr missing/too short")
        if not isinstance(item.get("locator"), str) or not item["locator"]:
            fail(f"{item_id}: locator required")

    for item in official:
        if item.get("source_id") != "TR.AFAD.TAMP.2022" or item.get("kind") != "official_context":
            fail(f"{item['id']}: invalid official source/kind")
    for item in practice:
        if item.get("source_id") != "IARU.R1.EMCOMM.PROCEDURES" or item.get("kind") != "amateur_practice":
            fail(f"{item['id']}: invalid practice source/kind")

    unsupported = data.get("unsupported_claims")
    if not isinstance(unsupported, list) or len(unsupported) < 5:
        fail("unsupported claim guard list incomplete")
    joined = " ".join(unsupported).lower()
    for token in ("yayın izni", "frekans", "görevlendirme", "yönetmeliğin tam", "iaru"):
        if token not in joined:
            fail(f"unsupported claim guard missing token: {token}")

    print(
        f"PASS: validated {len(official)} official-context item(s), "
        f"{len(practice)} amateur-practice item(s); legal/frequency permission inference disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
