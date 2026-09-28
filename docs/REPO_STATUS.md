# Repository Status — 2026-09-28

This file is the canonical human-readable **engineering closure snapshot** for Telsiz. Machine-readable source, rule and frequency data remain authoritative in `data/`. The engineering baseline below is the last verified commit that changed code/data/validation behavior; later documentation-only commits may advance `main` without changing that engineering baseline.

## Canonical engineering baseline

- Engineering baseline: `4d5f6b797218fffc6bc3729361232dfece15ea43`
- Technical closure PR: **#10**
- Open pull requests at technical-closure snapshot: **0**
- Main workflow: `Knowledge Validation`
- Main exact-head run: `36477656205`
- Status: `completed`
- Conclusion: `success`
- Runner: `GitHub Actions 1000014027`
- Completed workflow steps: **10**

The exact-head main job proves:

- tracked Python/cache artifact check: **PASS**
- source/rule/frequency registry validation: **PASS**
- BTK raw transcription validator: **PASS**
- unit test suite: **65 tests, OK**
- source registry: **11 records**
- grounded rules: **10 records**
- semantic frequency rows: **2 records**
- raw BTK amateur source rows: **33 records**
- Tablo 26-1 emission definitions: **24 records**
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

## P0 — BTK amateur frequency table

Canonical semantic file: `data/frequency_table.json`  
Canonical raw source transcription: `data/btk_amateur_table_raw.json`  
Emission reference: `data/btk_emission_types.json`

Current state:

```text
RAW_SOURCE_ROWS=33
RAW_ROW_TRANSCRIPTION=PASS
EMISSION_DEFINITIONS=24
SEMANTIC_FREQUENCY_ROWS=2
FREQUENCY_COVERAGE=PARTIAL
ARTIFACT_SHA256=UNKNOWN
SEMANTIC_PROMOTION=HOLD
```

The official BTK PDF was opened through a trusted PDF rendering path, its amateur table pages were visually verified, and all **33** visible source rows were transcribed. The raw transcription is now independently validated in CI.

The semantic table remains partial. Raw rows do **not** directly create an `ALLOWED` verdict.

Only the previously grounded semantic C-class limits remain decision-enabled:

- 144–146 MHz → maximum transmitter output power 5 W
- 430–440 MHz → maximum transmitter output power 5 W

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
TESTS=65/65
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

## Closure state

```text
REPOSITORY_CONTROLS=PASS
CI=PASS
ENGINEERING_BASELINE=4d5f6b797218fffc6bc3729361232dfece15ea43
RAW_BTK_ROWS=33
EMISSION_DEFINITIONS=24
TESTS=65
FREQUENCY_COVERAGE=PARTIAL
P0=RAW_TRANSCRIPTION_COMPLETE_SEMANTIC_PROMOTION_HOLD
P1=VERIFY_REQUIRED
P2=VERIFY_REQUIRED
P3=VERIFY_REQUIRED
```
