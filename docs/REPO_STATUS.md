# Repository Status — 2026-09-28

This file is the canonical human-readable closure snapshot for the current Telsiz repository state. Machine-readable source, rule and frequency data remain authoritative in `data/`.

## Canonical main baseline

- `main`: `88bf927e59503f6371295c2938aacaeb5952c772`
- Open pull requests at snapshot time: **0**
- Latest main workflow: `Knowledge Validation`
- Main run: `36470211240`
- Status: `completed`
- Conclusion: `success`
- Runner: `GitHub Actions 1000014000`
- Completed workflow steps: **9**

The CI job confirms:

- tracked Python/cache artifact check: **PASS**
- source/rule/frequency registry validation: **PASS**
- unit test suite: **53 tests, OK**
- source registry: **11 records**
- grounded rules: **10 records**
- frequency rows: **2 records**
- frequency coverage: **partial**

## Closed PR chain

| PR | Purpose | Head SHA | Merge SHA | Status |
|---|---|---|---|---|
| #5 | Frequency-table safety structure, fail-closed lookup and question→rule→source tests | `599a65b0290a3c6aacfa56cfe0700a7705e6b527` | `516a0a15645dbf75dd381b48ef07f6aad2eda28d` | MERGED |
| #6 | Remove accidentally tracked Python bytecode and add ignore protection | `fd38e029ab6716e4fb2b294a32d95dae5fa386d8` | `d39b042cd14a4c1ec65f88eb838f38d01f5b8dfd` | MERGED |
| #7 | Decision engine, completeness gate, source access log and tracked-cache regression CI | `d01a7dc479b938d4091cb6773361c80427d12965` | `88bf927e59503f6371295c2938aacaeb5952c772` | MERGED |

## Current frequency-table status

Canonical file: `data/frequency_table.json`

Current state:

```text
coverage_status=partial
coverage_blocker=BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
artifact=null
row_count_reconciliation=null
```

Only the already-grounded C-class power rows are present:

- 144–146 MHz → 5 W maximum transmitter output power
- 430–440 MHz → 5 W maximum transmitter output power

These rows are **not** a complete amateur frequency table.

For unextracted fields:

```text
null = NOT_EXTRACTED
```

`null` must never be interpreted as "no restriction" or "permission granted".

A missing row must not automatically become `NOT_ALLOWED`; incomplete evidence produces `UNKNOWN`.

## Official-source access blocker

The 2026-09-28 source probe recorded the following domains as blocked from the Claude Code cloud environment by egress policy:

- `www.btk.gov.tr`
- `www.mevzuat.gov.tr`
- `www.resmigazete.gov.tr`
- `resmigazete.gov.tr`

Observed failure class: `CONNECT 403 / EGRESS_BLOCKED`.

Therefore:

```text
P0 full BTK amateur frequency table = BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
P1 5809 full-text verification       = BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
P2 FTM Regulation verification      = BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
P3 KEGM Regulation verification     = BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
```

This blocker describes the execution environment, not the availability or validity of the official sources themselves.

No unofficial mirror, forum, community copy or memory-derived completion may be used to bypass this blocker.

See: [Official source access log](SOURCE_ACCESS_LOG.md).

## Fail-closed controls now enforced

The repository currently enforces these controls programmatically:

1. verified legal claims require verified source records;
2. legal rules require `official_legal` sources;
3. verified legal rules require current legal sources;
4. pending sources cannot support verified legal rules;
5. amateur-association material cannot create Turkish legal permission;
6. unknown/missing frequency information resolves to `UNKNOWN`, not fabricated permission or prohibition;
7. a table cannot be marked `complete` without official artifact evidence, matching SHA-256, row/footnote reconciliation and fully extracted row fields;
8. conflicting overlapping frequency rows are rejected;
9. tracked `.pyc`, `__pycache__`, `.pytest_cache`, `.mypy_cache` and `.ruff_cache` artifacts fail CI.

## Source artifact policy

When official access becomes available:

1. fetch the official artifact;
2. record canonical URL, fetch time, HTTP status, MIME type, size and page count;
3. calculate SHA-256;
4. bind the hash to the source record;
5. extract rows/rules with exact source locators;
6. reconcile source row and footnote counts;
7. run the full validator and tests;
8. only then permit `coverage_status=complete`.

If the same source URL later produces a different SHA-256, derived data returns to:

```text
SOURCE_CHANGED
REVERIFY_REQUIRED
```

until rechecked.

## Google Drive companion documentation

The `Telsiz_AI_Knowledge_Base` Drive structure exists as a human-readable companion store. The latest synchronization includes separate records for:

- PR #6 cleanup evidence;
- PR #7 work log;
- official source access probe;
- frequency decision contract;
- PR #7 test-suite evidence.

Drive file identifiers are intentionally not duplicated in this repository. GitHub remains the canonical store for code, structured data, validation logic and exact commit history.

## NEXT

Once official-source access is available, continue in this order:

1. P0 — fetch the official BTK technical-criteria PDF, record SHA-256, extract and reconcile the full amateur frequency table;
2. P1 — verify and atomize relevant provisions of Law No. 5809;
3. P2 — verify and atomize the FTM Regulation;
4. P3 — verify and atomize the KEGM amateur-radio examination/certification regulation;
5. expand licence/call-sign and technical knowledge only from source-grounded material.

## Closure state

```text
REPOSITORY_CONTROLS=PASS
CI=PASS
CURRENT_MAIN=88bf927e59503f6371295c2938aacaeb5952c772
FREQUENCY_COVERAGE=PARTIAL
P0=BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
P1=BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
P2=BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
P3=BLOCKED_BY_OFFICIAL_SOURCE_ACCESS
```
