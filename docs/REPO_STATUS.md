# Repository Status — 2026-09-28

This file is the canonical human-readable **engineering closure snapshot** for Telsiz. Machine-readable source, rule and frequency data remain authoritative in `data/`. The engineering baseline below is the last verified commit that changed code/data/validation behavior; later documentation-only commits may advance `main` without changing that engineering baseline.

## Canonical engineering baseline

- Engineering baseline: `dec037601a1aacc255b25e50b7b2200d54c86ded`
- Technical closure PR: **#32**
- Open pull requests at technical-closure snapshot: **0**
- Main workflow: `Knowledge Validation`
- Main exact-head run: `36554094775`
- Status: `completed`
- Conclusion: `success`
- Runner: `GitHub Actions 1000014173`
- Completed workflow steps: **19**

The exact-head main job proves:

- tracked Python/cache artifact check: **PASS**
- source/rule/frequency registry validation: **PASS**
- BTK raw transcription validator: **PASS**
- unit test suite: **246 tests, OK**
- source registry: **22 records**
- grounded rules: **10 records**
- semantic frequency rows: **7 records**
- raw BTK amateur source rows: **33 records**
- Tablo 26-1 emission definitions: **24 records**
- official artifact registry: **1 record, awaiting_bytes, fail-closed**
- Academy manifest: **10 modules**
- repeater operational snapshot: **15 TRAC rows, association-only authority**
- bilingual navigation translations: **2 validated entries**
- semantic frequency coverage: **partial**

## Closed PR chain

| PR | Purpose | Head SHA | Merge SHA | Status |
|---|---|---|---|---|
| #5 | Frequency-table safety structure, fail-closed lookup and question→rule→source tests | `599a65b0290a3c6aacfa56cfe0700a7705e6b527` | `516a0a15645dbf75dd381b48ef07f6aad2eda28d` | MERGED |
| #6 | Remove accidentally tracked Python bytecode and add ignore protection | `fd38e029ab6716e4fb2b294a32d95dae5fa386d8` | `d39b042cd14a4c1ec65f88eb838f38d01f5b8dfd` | MERGED |
| #7 | Decision engine, completeness gate, source access log and tracked-cache regression CI | `d01a7dc479b938d4091cb6773361c80427d12965` | `88bf927e59503f6371295c2938aacaeb5952c772` | MERGED |
| #8 | Canonical repository closure-status document | `39fad23342d1a7faed409f4dd726a0277da60f4e` | `0085b3ad910fba86095edcf7f4cf5f598867c7a2` | MERGED |
| #9 | Distinguish moving main from engineering baseline | `6f6b2fefc7a68e926a98a1455e2e317282afc9f6` | `b6c4a03bde0f6b71024a3065199c2989bcf35e0d` | MERGED |
| #10 | Official BTK amateur-table raw extraction, emission map and raw-integrity gate | `341e74206a7adb42ed8d87b0d96af85d7dc010c2` | `4d5f6b797218fffc6bc3729361232dfece15ea43` | MERGED |
| #12 | Byte-level official artifact registry, SHA-256/change-detection gate and tests | `28cb04215581fe629eafb1996d06ca30b7352038` | `0c2b5952b551d485f3530374447fbd2040605b03` | MERGED |
| #14 | Split C-class 430–440 MHz power condition into the six visible BTK source sub-bands and reject gap inference | `8fb4dbae0c2167a85ff86af87b07d3afde3df2db` | `fd3bf6bb6290da92dea8a2ce73cffee094271cc1` | MERGED |
| #15 | Add fail-closed unverified source-candidate registry and candidate validation/tests | `9f645e2c9cd77daf46ab6ca85bdd02bab41d60da` | `3a8c2d5297907277b482b71eee63129e9e352ffa` | MERGED |
| #16 | Correct community-reference identity/access state and add source-safe P11 adaptation backlog | `3d0aaa1adce6e0e56ea0de16ca0e737c9401517a` | `8765783514ba72569d7964aaf5ac19ae75b13e7f` | MERGED |

## P0 — BTK amateur frequency table

Canonical semantic file: `data/frequency_table.json`  
Canonical raw source transcription: `data/btk_amateur_table_raw.json`  
Emission reference: `data/btk_emission_types.json`

Current state:

```text
RAW_SOURCE_ROWS=33
RAW_ROW_TRANSCRIPTION=PASS
EMISSION_DEFINITIONS=24
SEMANTIC_FREQUENCY_ROWS=7
FREQUENCY_COVERAGE=PARTIAL
ARTIFACT_SHA256=UNKNOWN
SEMANTIC_PROMOTION=HOLD
```

The official BTK PDF was opened through a trusted PDF rendering path, its amateur table pages were visually verified, and all **33** visible source rows were transcribed. The raw transcription is now independently validated in CI.

The semantic table remains partial. Raw rows do **not** directly create an `ALLOWED` verdict.

Only the previously grounded semantic C-class limits remain decision-enabled:

- 144–146 MHz → maximum transmitter output power 5 W
- 430–440 MHz C-class power condition → six visible BTK sub-bands are represented semantically at 5 W; gaps remain `UNKNOWN`

For unextracted semantic dimensions:

```text
null = NOT_EXTRACTED
```

A missing or unresolved semantic field produces `UNKNOWN`, not fabricated permission.

## Remaining P0 gate

The source-content access blocker has been reduced substantially: the official PDF content is available through a trusted renderer and the raw table is reconciled 33/33.

P0 is **not** fully complete because byte-level artifact evidence is still missing and source-internal conflicts remain open:

1. raw official PDF bytes must be acquired from the same canonical URL;
2. file size and SHA-256 must be recorded;
3. source registry must bind that hash;
4. source-change detection must compare later downloads;
5. raw rows must be promoted into conflict-aware semantic records;
6. open source conflicts must not be silently normalized.

Current status:

```text
P0=RAW_TRANSCRIPTION_COMPLETE_SEMANTIC_PROMOTION_HOLD
P0_ARTIFACT_GATE=PASS
P0_ARTIFACT_STATUS=AWAITING_BYTES
P0_BLOCKER=ARTIFACT_SHA256_AND_SOURCE_CONFLICTS
```

## Open official-source conflicts

- `TR-BTK-NUMBERING-001` — Article 22 refers to Table-26 while the visible amateur-table heading is Table 25.
- `TR-BTK-EMISSION-001` — the merged emission cell repeats source tokens and contains `A3J`/`J2C`, while Tablo 26-1 does not define those two codes. No silent substitution is permitted.
- `TR-BTK-UNIT-001` — the 28000–29700 kHz row contains a B-class condition sentence written as 28000–29700 MHz. No silent unit correction is permitted.

See [Known source conflicts](SOURCE_CONFLICTS.md) and [BTK raw extraction evidence](BTK_RAW_EXTRACTION.md).

## Fail-closed controls

The repository currently enforces these controls programmatically:

1. verified legal claims require verified source records;
2. legal rules require `official_legal` sources;
3. verified legal rules require current legal sources;
4. pending sources cannot support verified legal rules;
5. amateur-association material cannot create Turkish legal permission;
6. unknown/missing semantic frequency information resolves to `UNKNOWN`;
7. semantic coverage cannot become `complete` without artifact evidence, SHA-256, reconciliation and required extracted dimensions;
8. conflicting overlapping semantic rows are rejected;
9. raw BTK transcription must contain exactly 33 source rows and 24 emission definitions;
10. source-only undefined emission anomalies are explicitly preserved rather than normalized;
11. repeated source emission tokens are de-duplicated only in the machine list while provenance records the anomaly;
12. tracked Python/cache artifacts fail CI.
13. semantic frequency rows must lie inside a visible raw BTK row that lists the same licence class;
14. source candidates are discovery-only and cannot ground rules/frequency rows;
15. non-official source candidates must explicitly disclaim legal-claim authority;
16. community reference material remains separate from legal/official source layers.

## CI learning from PR #10

Two pre-merge runs correctly failed when inherited merged-cell emission repetitions were present in machine-readable arrays. The validator was **not weakened**. The data was corrected, source anomalies were documented, and a regression test was added across every raw row.

Final exact-head evidence:

```text
PR_HEAD=341e74206a7adb42ed8d87b0d96af85d7dc010c2
PR_RUN=36477491102
PR_RUNNER=GitHub Actions 1000014026
PR_CI=PASS

MERGE_SHA=4d5f6b797218fffc6bc3729361232dfece15ea43
MAIN_RUN=36477656205
MAIN_RUNNER=GitHub Actions 1000014027
MAIN_CI=PASS
TESTS=75/75
RAW_ROWS=33/33
EMISSION_DEFINITIONS=24/24
```

## Google Drive companion documentation

The `Telsiz_AI_Knowledge_Base` Drive tree is the human-readable companion store. GitHub remains canonical for code, structured data, validators and commit history. New PR #10 evidence should be stored as a delta/readback record rather than overwriting an existing log when the Drive interface cannot edit it safely.

## NEXT

Continue fail-closed in this order:

1. **P0 artifact gate** — acquire the canonical official PDF bytes, calculate SHA-256/file size, bind the hash and activate source-change detection.
2. **P0 semantic promotion** — map the 33 raw rows into semantic class/power/emission/context records without normalizing open conflicts.
3. **P1** — exact-text verification and atomization of relevant Law No. 5809 provisions.
4. **P2** — exact-text verification and atomization of the FTM Regulation.
5. **P3** — exact-text verification and atomization of the KEGM amateur-radio examination/certification regulation.
6. Expand licence/call-sign and technical knowledge only from source-grounded material.
7. **P11** — implement academy/operator-tool features only on top of the grounded source/rule/data chain.

## Closure state

```text
REPOSITORY_CONTROLS=PASS
CI=PASS
ENGINEERING_BASELINE=dec037601a1aacc255b25e50b7b2200d54c86ded
RAW_BTK_ROWS=33
EMISSION_DEFINITIONS=24
TESTS=246
FREQUENCY_COVERAGE=PARTIAL
P0=RAW_TRANSCRIPTION_COMPLETE_SEMANTIC_PROMOTION_HOLD
P1=VERIFY_REQUIRED
P2=VERIFY_REQUIRED
P3=VERIFY_REQUIRED
```


## PR #12 — official artifact gate closure

The byte-level artifact workflow is now a first-class fail-closed control.

```text
PR12_HEAD=28cb04215581fe629eafb1996d06ca30b7352038
PR12_PUSH_RUN=36478546832
PR12_PUSH_RUNNER=GitHub Actions 1000014035
PR12_PR_RUN=36478618168
PR12_PR_RUNNER=GitHub Actions 1000014036
PR12_MERGE_SHA=0c2b5952b551d485f3530374447fbd2040605b03
PR12_MAIN_RUN=36478669415
PR12_MAIN_RUNNER=GitHub Actions 1000014037
PR12_CI=PASS
TESTS=75/75
ARTIFACT_RECORDS=1
BTK_ARTIFACT_STATUS=awaiting_bytes
BTK_ARTIFACT_SHA256=UNKNOWN
```

The gate distinguishes rendered/read content from byte-for-byte artifact verification. It calculates SHA-256 from local bytes, checks PDF signature/MIME/size, and produces `HASH_OBSERVED_BIND_REQUIRED`, `UNCHANGED`, or `SOURCE_CHANGED` + `REVERIFY_REQUIRED`.

Infrastructure PASS is **not** evidence that the BTK artifact bytes have been verified. The current BTK artifact record intentionally remains `awaiting_bytes`.

## P1 — Law No. 5809 status

Fresh official BTK pages expose and attribute provisions from Articles 36, 37, 40 and 63 of Law No. 5809, which is useful corroborating evidence. The canonical `mevzuat.gov.tr` law artifact still could not be fetched in the current verification path.

Therefore:

```text
P1=VERIFY_REQUIRED
P1_CANONICAL_TEXT=UNAVAILABLE_IN_CURRENT_PATH
P1_RULE_PROMOTION=HOLD
```

No pending EHK source is promoted to verified legal authority from a secondary official quotation alone.


## PR #14–#16 — current closure delta

The repository advanced beyond the PR #12 artifact-gate baseline.

### PR #14 — C-class 430–440 MHz gap-safety correction

The former continuous semantic row was split into the six visible BTK source sub-bands. Frequencies in the gaps no longer inherit a 5 W match merely because they lie numerically inside 430–440 MHz.

### PR #15 — source candidate registry

Unverified future sources are now isolated in `data/source_candidates.json`. Candidates cannot ground rules or semantic frequency rows and non-official candidates cannot support legal claims.

### PR #16 — community reference correction / P11 backlog

The exact public repository `arch-yunus/Amator-Telsiz-Rehberi` was independently rechecked as reachable and MIT-licensed. Its status was corrected from `candidate_inaccessible` to `candidate_unverified`; it remains community-level and cannot create Turkish permission or verified legal/technical claims.

Exact-head evidence:

```text
PR16_HEAD=3d0aaa1adce6e0e56ea0de16ca0e737c9401517a
PR16_RUN=36482367962
PR16_JOB=109130864727
PR16_CI=PASS
PR16_TESTS=104/104

PR16_MERGE_SHA=8765783514ba72569d7964aaf5ac19ae75b13e7f
MAIN_RUN=36482477669
MAIN_JOB=109131223968
MAIN_RUNNER=GitHub Actions 1000014052
MAIN_CI=PASS
MAIN_TESTS=104/104
```

P0 artifact verification remains intentionally unresolved:

```text
BTK_PDF_RENDER_ACCESS=PASS
BTK_PDF_RAW_BYTES=UNAVAILABLE_IN_RUNTIME
BTK_ARTIFACT_SHA256=UNKNOWN
P0_ARTIFACT_STATUS=AWAITING_BYTES
```

Render access is not treated as byte-level artifact verification.


## PR #17–#33 — current engineering delta

The repository advanced materially beyond the PR #16 baseline. The current engineering baseline is the bilingual implementation merge; the following PR #33 is documentation-only closure evidence.

### Key merged capabilities

- PR #19 — fail-closed Academy manifest and validator.
- PR #21 — deterministic Maidenhead Grid Locator.
- PR #22 — ITU-grounded Morse trainer.
- PR #23 — source-grounded Q-code and RS(T) trainer.
- PR #24 — bounded ADIF 3.1.7 QSO-log exporter.
- PR #25 — source-grounded RF wavelength calculator.
- PR #26 — fail-closed Yaesu FTM-400 device/firmware guard.
- PR #27 — authority-separated TRAC repeater operational registry.
- PR #28 — exact-head runner evidence enforcement.
- PR #29 — SHA-pinned Node 24 GitHub Actions.
- PR #32 — fail-closed bilingual documentation and drift validation.
- PR #33 — bilingual closure evidence only.

### Current exact-head evidence

```text
ENGINEERING_BASELINE=dec037601a1aacc255b25e50b7b2200d54c86ded
CURRENT_MAIN=1e7d599aca08d52456ec04775cb3fae0b5ce7b48
MAIN_RUN=36554094775
MAIN_JOB=109358983262
MAIN_RUNNER=GitHub Actions 1000014173
MAIN_CI=completed/success
WORKFLOW_STEPS=19
TESTS=246/246
SOURCE_RECORDS=22
GROUNDED_RULES=10
SEMANTIC_FREQUENCY_ROWS=7
SOURCE_CANDIDATES=15
RAW_BTK_ROWS=33/33
EMISSION_DEFINITIONS=24/24
ARTIFACT_RECORDS=1
ACADEMY_MODULES=10
REPEATER_SNAPSHOT_ROWS=15
BILINGUAL_TRANSLATIONS=2
OPEN_PRS=0
```

### Authority / safety boundaries retained

- TRAC repeater operational status remains association-level information and does not become BTK permission.
- Bilingual/English navigation remains subordinate to canonical Turkish/source-backed content.
- Device firmware instructions remain region/family gated.
- Academy/practice tools do not bypass the legal decision engine.
- P0 remains partial while BTK byte-artifact SHA-256 is unknown.
- P1/P2/P3 remain fail-closed until canonical consolidated texts are verified.

## Current NEXT

1. **P0 byte artifact** — acquire the canonical BTK PDF bytes, calculate file size + SHA-256, bind the hash and run source-change detection.
2. **P0 semantic promotion** — continue mapping raw rows into semantic records only where source conflicts do not require silent correction.
3. **P1–P3** — verify consolidated official legal texts before promoting legal rules.
4. Continue P11/operator tooling only where it cannot weaken the authority hierarchy above.


## 2026-09-29 — P0 byte-artifact baseline closure delta

The historical sections above preserve earlier closure snapshots. This delta supersedes only the BTK byte-artifact status.

Exact observation evidence:

```text
PROBE_HEAD=5472204e5f9fcf9beee5219c724814259cbee42c
KNOWLEDGE_RUN=36559259428
KNOWLEDGE_JOB=109375881490
KNOWLEDGE_CI=PASS
TESTS=254/254

ARTIFACT_RUN=36559259435
ARTIFACT_JOB=109375881365
ARTIFACT_RUNNER=GitHub Actions 1000014181
ARTIFACT_EXACT_HEAD=PASS
BTK_FETCHED_AT=2026-09-29T11:02:27Z
BTK_SIZE_BYTES=508766
BTK_SHA256=eff832fc30df1adf60e4a8c514a6069154d526d3ab88ae803b51a5536d103db0
INITIAL_CHANGE_STATUS=HASH_OBSERVED_BIND_REQUIRED
FINAL_BOUND_STATUS=verified_bytes/UNCHANGED
REVERIFY_REQUIRED=false
```

The registered canonical HTTPS URL and final download URL were identical. The byte baseline was reviewed and explicitly bound to `TR.BTK.FTM.TECH.2022-IK-SYD-245`; no PDF binary is committed to GitHub.

Current P0 state after this delta:

```text
P0_ARTIFACT_GATE=PASS
P0_ARTIFACT_STATUS=VERIFIED_BYTES
P0_ARTIFACT_SHA256=BOUND
P0_BYTE_BLOCKER=CLOSED
P0_SEMANTIC_PROMOTION=HOLD
P0_BLOCKER=SOURCE_CONFLICTS_AND_SEMANTIC_PROMOTION
```

Open source conflicts remain unchanged: `TR-BTK-NUMBERING-001`, `TR-BTK-EMISSION-001`, and `TR-BTK-UNIT-001`. No source anomaly is silently normalized.
