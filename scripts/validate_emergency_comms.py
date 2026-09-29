#!/usr/bin/env python3
"""Validate emergency communications source separation and claims."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "emergency_comms.json"
SOURCES = ROOT / "data" / "sources.json"
CANDIDATES = ROOT / "data" / "source_candidates.json"

CURRENT_LEGAL_ID = "TR.AFAD.MUDAHALE.REGULATION.2025-10809"
HISTORICAL_LEGAL_ID = "TR.AFAD.MUDAHALE.REGULATION.2022-5211"
CURRENT_CANDIDATE_ID = "CAND.TR.RG.AFAD.MUDAHALE.REGULATION.2025-10809"
OLD_CANDIDATE_ID = "CAND.TR.AFAD.MUDAHALE_REGULATION.2022"
CURRENT_RG_URL = "https://www.resmigazete.gov.tr/eskiler/2025/12/20251231M5-15.pdf"

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
    candidates = {s["id"]: s for s in load(CANDIDATES)["candidates"]}

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


    current = sources.get(CURRENT_LEGAL_ID)
    historical = sources.get(HISTORICAL_LEGAL_ID)
    if current is None:
        fail("current 10809 legal source record missing")
    if historical is None:
        fail("historical 5211 legal source record missing")

    if current.get("source_type") != "official_legal":
        fail("current 10809 source must be official_legal")
    if current.get("verification_status") != "pending":
        fail("current 10809 source must remain pending until origin exact text is fetched")
    if current.get("legal_status") != "current" or current.get("instrument_id") != "10809":
        fail("current 10809 source legal metadata mismatch")
    if current.get("url") != CURRENT_RG_URL:
        fail("current 10809 source must use exact Resmi Gazete URL")
    if current.get("verified_at") is not None:
        fail("pending current 10809 source must not have verified_at")
    if HISTORICAL_LEGAL_ID not in current.get("supersedes", []):
        fail("current 10809 source must supersede historical 5211")

    if historical.get("source_type") != "official_legal":
        fail("historical 5211 source must be official_legal")
    if historical.get("verification_status") != "verified":
        fail("historical 5211 source must be verified")
    if historical.get("legal_status") != "repealed" or historical.get("instrument_id") != "5211":
        fail("historical 5211 source status mismatch")
    if CURRENT_LEGAL_ID not in historical.get("superseded_by", []):
        fail("historical 5211 source must point to current 10809")

    if "[STALE_LEGAL_BASIS_METADATA]" not in sources["TR.AFAD.TAMP.2022"].get("notes", ""):
        fail("TAMP source must explicitly mark stale 2022 legal-basis metadata")

    if OLD_CANDIDATE_ID in candidates:
        fail("obsolete 2022 AFAD candidate must be removed")
    cand = candidates.get(CURRENT_CANDIDATE_ID)
    if cand is None:
        fail("current 10809 exact-text candidate missing")
    if cand.get("status") != "candidate_inaccessible":
        fail("current 10809 candidate must remain inaccessible until origin fetch succeeds")
    if cand.get("canonical_url") is not None:
        fail("current 10809 candidate canonical_url must remain null until promotion")

    contract = data.get("authority_contract", {})
    if contract.get("current_legal_source_id") != CURRENT_LEGAL_ID:
        fail("authority contract current legal source mismatch")
    if contract.get("current_legal_exact_text_status") != "PENDING_ORIGIN_FETCH":
        fail("current legal exact-text status must remain pending")
    if contract.get("tamp_page_legal_basis_metadata") != "STALE":
        fail("TAMP legal-basis metadata must be marked stale")
    if contract.get("historical_2022_regulation_status") != "REPEALED":
        fail("historical 2022 regulation must be marked repealed")
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

    guard = data.get("legal_status_guard", {})
    if guard.get("current_source_id") != CURRENT_LEGAL_ID:
        fail("legal status guard current source mismatch")
    if guard.get("historical_source_id") != HISTORICAL_LEGAL_ID:
        fail("legal status guard historical source mismatch")
    if guard.get("historical_status") != "REPEALED":
        fail("legal status guard must mark 5211 repealed")
    if guard.get("tamp_page_legal_basis_metadata") != "STALE":
        fail("legal status guard must mark TAMP metadata stale")
    if guard.get("current_exact_text_verification") != "PENDING_ORIGIN_FETCH":
        fail("legal status guard must fail closed on origin exact-text")
    if guard.get("legal_rule_promotion_enabled") is not False:
        fail("legal rule promotion must remain disabled")
    warning = guard.get("warning_tr", "")
    for token in ("5211", "10809", "güncel değildir", "hukuki"):
        if token not in warning:
            fail(f"legal status warning missing token: {token}")

    unsupported = data.get("unsupported_claims")
    if not isinstance(unsupported, list) or len(unsupported) < 5:
        fail("unsupported claim guard list incomplete")
    joined = " ".join(unsupported).lower()
    for token in ("yayın izni", "frekans", "görevlendirme", "yönetmeliğin tam", "iaru"):
        if token not in joined:
            fail(f"unsupported claim guard missing token: {token}")

    print(
        f"PASS: validated {len(official)} official-context item(s), "
        f"{len(practice)} amateur-practice item(s); current-law gate pending exact origin fetch; legal/frequency permission inference disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
