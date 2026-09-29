# Emergency communications source layer closure — 2026-09-29

## FOUND

Telsiz had no grounded disaster/emergency communications source layer. The coverage map still treated this domain as missing.

## ROOT_CAUSE

Emergency communications mix several authority levels: official disaster-response coordination, amateur operating practice, and actual legal permission to transmit. Combining these into one unqualified source layer would let lower-authority guidance appear to create legal permission, frequency entitlement, or official assignment.

## SCOPE

Verified contextual sources:

- `TR.AFAD.TAMP.2022` — AFAD/TAMP official technical coordination context.
- `IARU.R1.EMCOMM.PROCEDURES` — IARU Region 1 amateur training/operating practice.

Tracked legal gap:

- `CAND.TR.AFAD.MUDAHALE_REGULATION.2022` — full official text/provenance of Afet ve Acil Durum Müdahale Hizmetleri Yönetmeliği; not yet promoted.

## FIX

- added `data/emergency_comms.json`;
- added 5 AFAD official-context records;
- added 4 IARU amateur-practice records;
- added `scripts/validate_emergency_comms.py`;
- added `scripts/emergency_comms.py`;
- routed emergency/TAMP/S1–S4 queries through `ask.py`;
- numeric emergency-frequency questions continue through the existing BTK decision path;
- added fail-closed negative tests;
- added the emergency validator to exact-head CI;
- updated knowledge coverage and candidate documentation.

## FAIL-CLOSED CONTRACT

```text
LEGAL_PERMISSION_FROM_THIS_LAYER=PROHIBITED
FREQUENCY_INFERENCE=PROHIBITED
AMATEUR_STATUS_IMPLIES_OFFICIAL_ASSIGNMENT=false
EMERGENCY_CONTEXT_EXPANDS_TRANSMIT_PERMISSION=false
IARU_CAN_OVERRIDE_TURKISH_LEGAL_AUTHORITY=false
AFAD_SUMMARY_SUBSTITUTES_FULL_REGULATION=false
```

## FAILURE LEARNING

### Failure 1 — invalid phase

```text
HEAD=4a0406183412c20ec82b25de278afd42130c1c8b
RUN=36599086396
JOB=109511494313
RUNNER=GitHub Actions 1000014257
RESULT=FAIL
ROOT_CAUSE=CAND.TR.AFAD.MUDAHALE_REGULATION.2022 used noncanonical P12
FIX=move candidate to canonical P8
PREVENTION=source-candidate validator already enforces P0-P11
```

### Failure 2 — unit/doc drift

```text
HEAD=3bf3193157f763fa0f003f94815f93bd9ed8c25a
RUN=36599152497
JOB=109511720029
RUNNER=GitHub Actions 1000014258
RESULT=FAIL
ROOT_CAUSE_1=Unicode dotted-I brittle assertion for BİLİNMİYOR
FIX_1=assert semantic 'karar:' marker instead
ROOT_CAUSE_2=SOURCE_CANDIDATES.md did not list new AFAD legal-text candidate and still listed promoted IARU candidate
FIX_2=synchronize docs with data/source_candidates.json
PREVENTION=existing candidate-doc parity test retained
```

## PASS EVIDENCE

```text
PUSH_HEAD=777a59733c9c1fa866e30cccbaf9bd4944c4c774
PUSH_RUN=36599247213
PUSH_JOB=109512046114
PUSH_RUNNER=GitHub Actions 1000014260
PUSH_CI=PASS
PUSH_TESTS=413/413

PR=50
PR_RUN=36599522523
PR_JOB=109512991387
PR_RUNNER=GitHub Actions 1000014261
PR_CI=PASS
PR_TESTS=413/413

ENGINEERING_MERGE_SHA=0527b1dab90427768db5115817844ed304eaf5cd
MAIN_RUN=36599606656
MAIN_JOB=109513284784
MAIN_RUNNER=GitHub Actions 1000014262
MAIN_CI=PASS
MAIN_TESTS=413/413
```

## STATUS

```text
FOUND=missing emergency communications grounding
ROOT_CAUSE=authority layers were not modeled separately
FIX=AFAD context + IARU practice + fail-closed legal boundary
VALIDATION=PASS
CI=PASS
GITHUB_TECHNICAL_MERGE=PASS
ENGINEERING_BASELINE=0527b1dab90427768db5115817844ed304eaf5cd
LEGAL_RULE_PROMOTION_FROM_AFAD_SUMMARY=DISABLED
STATUS=ENGINEERING_CLOSED
NEXT=verify full official 2022 regulation text/provenance
STOP_REASON=none
```
