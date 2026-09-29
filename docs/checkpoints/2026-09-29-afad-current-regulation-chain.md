# AFAD current regulation / TAMP legal-basis verification — 2026-09-29

## FOUND

The emergency layer's original legal verification target was outdated. The AFAD TAMP page still points to the 24.02.2022 / 5211 regulation, while the current Afet ve Acil Durum Müdahale Hizmetleri Yönetmeliği is the 31.12.2025 / 10809 instrument.

## ROOT_CAUSE

A current institutional TAMP page preserved historical 2022 legal-basis metadata. Treating that page as a current-law source would conflate current operational context with an obsolete legal reference.

## SCOPE

```text
CURRENT_SOURCE=TR.AFAD.MUDAHALE.REGULATION.2025-10809
CURRENT_INSTRUMENT=10809
CURRENT_PUBLICATION_DATE=2025-12-31
CURRENT_EFFECTIVE_DATE=2025-12-31
CURRENT_SOURCE_STATUS=pending
CURRENT_LEGAL_STATUS=current

HISTORICAL_SOURCE=TR.AFAD.MUDAHALE.REGULATION.2022-5211
HISTORICAL_INSTRUMENT=5211
HISTORICAL_SOURCE_STATUS=verified
HISTORICAL_LEGAL_STATUS=repealed

TAMP_CONTEXT_SOURCE=TR.AFAD.TAMP.2022
TAMP_PAGE_2022_LEGAL_BASIS_METADATA=STALE
```

## FIX

- registered 2022/5211 as historical/repealed;
- registered 2025/10809 as current but exact-text pending;
- removed the obsolete 2022 current-law candidate;
- created `CAND.TR.RG.AFAD.MUDAHALE.REGULATION.2025-10809` for origin exact-text/byte verification;
- kept candidate `canonical_url=null` per repository policy;
- kept the exact Official Gazette URL on the pending current source record;
- marked the AFAD TAMP page's 2022 legal-basis metadata stale;
- added machine-enforced supersession/currentness guards;
- made TAMP answers display the current-law warning;
- updated source access, coverage, candidate and emergency-layer documentation.

## FAIL-CLOSED CONTRACT

```text
CURRENT_ORIGIN_EXACT_TEXT=PENDING_ORIGIN_FETCH
CURRENT_SOURCE_VERIFICATION=pending
LEGAL_RULE_PROMOTION=DISABLED
TAMP_PAGE_LEGAL_BASIS_AS_CURRENT=PROHIBITED
MIRROR_PROMOTION_TO_LEGAL_AUTHORITY=PROHIBITED
EMERGENCY_LAYER_PERMISSION_INFERENCE=PROHIBITED
```

## FAILURE LEARNING

Initial PR exact-head:

```text
HEAD=df2ac413fec0039e3cb5b22f891d6813b6aca6f8
RUN=36601666185
JOB=109520322229
RUNNER=GitHub Actions 1000014265
RESULT=FAIL
ROOT_CAUSE=CAND.TR.RG.AFAD.MUDAHALE.REGULATION.2025-10809 claimed canonical_url
FIX=candidate canonical_url restored to null; exact URL remains on current pending source
PREVENTION=source-candidate invariant retained and current-law validator added
```

Corrected PR exact-head:

```text
HEAD=fdedf0482a44f2c3ba563c6a08e688605ddd470d
RUN=36601747331
JOB=109520598043
RUNNER=GitHub Actions 1000014266
CI=PASS
TESTS=414/414 OK
CURRENT_LAW_GATE=PENDING_EXACT_ORIGIN_FETCH
```

Technical main exact-head:

```text
ENGINEERING_BASELINE=e6d415087d8e89eea8b724e17434aa52d0ca40b7
RUN=36602041554
JOB=109521572615
RUNNER=GitHub Actions 1000014267
CI=PASS
TESTS=414/414 OK
OPEN_PRS_AT_TECHNICAL_CLOSE=0
```

## STATUS

```text
FOUND=outdated 2022 current-law target
ROOT_CAUSE=stale legal-basis metadata on AFAD TAMP page
FIX=current/repealed provenance split + origin exact-text gate
VALIDATION=PASS
CI=PASS
CURRENTNESS_METADATA=VERIFIED
CURRENT_ORIGIN_EXACT_TEXT=PENDING
LEGAL_RULE_PROMOTION=HOLD
STATUS=ENGINEERING_CLOSED_FAIL_CLOSED
NEXT=origin 10809 PDF byte/exact-text verification
STOP_REASON=origin PDF body/raw bytes unavailable in active verification path
```
