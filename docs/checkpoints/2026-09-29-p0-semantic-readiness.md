# P0 semantic-promotion readiness checkpoint — 2026-09-29

## Scope

Advance the bound 33-row BTK raw transcription toward decision semantics without flattening source conflicts or conditional fields.

## BUILD

- bound raw transcription metadata to the verified BTK artifact SHA-256;
- created `data/btk_semantic_promotion.json` with exactly one readiness record for every raw row;
- classified power-model, emission-conflict and condition-model blockers;
- added validator `scripts/validate_semantic_promotion.py`;
- added the first new conflict-safe limited semantic row:
  - `TR.FTM.AMATEUR.ROW.AB.50-52`
  - A/B
  - 50–52 MHz
  - 100 W general output limit;
- kept emission, beacon, EME/satellite and special-condition fields null;
- kept overall frequency coverage partial.

## Source recheck

Official BTK PDF page 43/47 visibly shows the 50–52 MHz row with `100 W` and `A ve B`. The same page separately shows a 25 W beacon condition, so beacon semantics are not collapsed into the 100 W general row.

## CHECK

JSON-level comparison confirmed that the existing 10 rule objects are unchanged. The only new rule is:

`TR.AMATEUR.AB_50_52_MAX_100W`

## VERIFY CI

```text
HEAD=84e914174777889362c495b73bb34124b894fabe
RUN=36561023042
JOB=109381646523
RUNNER=GitHub Actions 1000014200
EXACT_HEAD=PASS
RAW_VALIDATOR=33 rows / 24 emissions PASS
ARTIFACT_REGISTRY=1 record PASS
SEMANTIC_READINESS=33 rows / 8 partial / 25 not-ready PASS
UNIT_TESTS=273/273 OK
FINAL_EXACT_HEAD=PASS
```

## STATUS

```text
P0_BYTE_BLOCKER=CLOSED
P0_READINESS_MAP=PASS
P0_SEMANTIC_COVERAGE=PARTIAL
P0_SEMANTIC_PROMOTION=HOLD
```

Next work must model unresolved power bases/multivalue PEP and conditional-use semantics or resolve the recorded source conflicts. No conflict is silently normalized.
