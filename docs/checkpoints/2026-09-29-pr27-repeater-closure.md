# PR #27 Repeater Registry Closure — 2026-09-29

## FOUND

PR #27 had originally been validated against an older main base and later became stale as `main` advanced.

Original historical state:

```text
OLD_BASE=8f4a3a4326d1464c75778084ca917bb26d3d2a0c
OLD_HEAD=5b1c7d86d08a51fb25ab52a29073189a995fc987
```

The original head was preserved before reintegration:

```text
SAFETY_BRANCH=safety/pr27-preintegrate-5b1c7d8
```

## ROOT_CAUSE

Parallel repository development advanced the current main branch after the original PR #27 CI evidence was produced. Historical PASS evidence was therefore insufficient for a merge under the repository fail-closed exact-head policy.

## SCOPE

P11.5 — authority-separated repeater and operating-practice registry.

The feature adds:

- verified operational source `TR.TRAC.REPEATER.LIST`;
- partial TRAC repeater snapshot;
- repeater lookup helper;
- snapshot validator and tests;
- Academy repeater documentation/module;
- explicit separation of association operational status from official BTK permission context.

## FIX

PR #27 was rebuilt on the then-current verified main:

```text
INTEGRATION_BASE=8adfd27e8111e9cce641d17ca23f8f8e09b98443
FINAL_PR_HEAD=c8a71557c612413caf18fb334c68e68942f2461f
```

Three-way inspection found that only `.github/workflows/knowledge-validation.yml` had independently changed on main among the PR's modified existing files.

The reintegration preserved main's:

- exact-head checkout/evidence gate;
- clean-worktree gate;
- SHA-pinned GitHub Actions;

and added only:

```text
Validate repeater operational snapshot
python scripts/validate_repeaters.py
```

Final comparison from integration base to PR head contained exactly the expected **14 files**.

## AUTHORITY SEPARATION

Operational repeater observations:

```text
SOURCE=TR.TRAC.REPEATER.LIST
AUTHORITY_CLASS=amateur_association
COVERAGE=partial_snapshot
RECORDS=15
```

Official permission/licensing context:

```text
SOURCE=TR.BTK.RADIO.PROCEDURES
AUTHORITY_CLASS=official_legal
```

Every association-derived repeater row remains:

```text
official_permission_status=UNKNOWN_NOT_VERIFIED
```

TRAC status such as `Aktif` or `Bakımda` is preserved as an operational observation and never converted into an official BTK permission verdict.

The 30-day stale threshold is explicitly a **Telsiz repository engineering policy**, not a claim attributed to TRAC or BTK.

## VALIDATION

Final PR-head push evidence:

```text
HEAD=c8a71557c612413caf18fb334c68e68942f2461f
PUSH_RUN=36552829937
PUSH_JOB=109354865906
PUSH_RUNNER=GitHub Actions 1000014155
PUSH_CI=completed/success
```

Final pull-request exact-head evidence:

```text
PR_RUN=36552888934
PR_JOB=109355053319
PR_RUNNER=GitHub Actions 1000014156
PR_CI=completed/success
EXACT_HEAD=PASS
WORKTREE=PASS
REPEATER_RECORDS=15
TESTS=240/240
```

## MERGE / MAIN EVIDENCE

PR #27 was squash merged:

```text
MERGE_SHA=5520a66e2334e0371a9a2a4c40dc62a21f7f93e4
MAIN_RUN=36552968602
MAIN_JOB=109355308829
MAIN_RUNNER=GitHub Actions 1000014157
MAIN_CI=completed/success
MAIN_TESTS=240/240
FINAL_EXACT_HEAD=PASS
FINAL_WORKTREE=PASS
OPEN_PRS_AFTER_MERGE=0
```

Post-merge main validation also reports:

- 22 source records;
- 10 grounded rules;
- 7 semantic frequency rows;
- 15 unverified source candidates;
- 33 raw BTK amateur rows;
- 24 emission definitions;
- 1 official artifact record;
- 10 Academy modules;
- 4 grounded practice-exam questions;
- 36 Morse mappings;
- 20 Q-code entries;
- 23 RS(T) entries;
- QSO/ADIF contract PASS;
- RF calculator PASS;
- Yaesu FTM-400 device registry PASS;
- 15-repeater operational snapshot PASS.

## P0 REMAINS FAIL-CLOSED

P11.5 completion does not change the legal-frequency artifact blocker:

```text
FREQUENCY_COVERAGE=partial
BTK_ARTIFACT_STATUS=awaiting_bytes
BTK_ARTIFACT_SHA256=UNKNOWN
P0_SEMANTIC_PROMOTION=HOLD
```

Open source conflicts remain:

- `TR-BTK-NUMBERING-001`
- `TR-BTK-EMISSION-001`
- `TR-BTK-UNIT-001`

## STATUS

```text
FOUND=stale PR base identified and safely reintegrated
ROOT_CAUSE=main advanced after historical PR CI
SCOPE=P11.5 repeater operational registry
FIX=rebuild on current main with workflow conflict resolved fail-closed
VALIDATION=240/240 tests; 15 repeater records; exact head/worktree PASS
CI=PASS on push, pull_request, and post-merge main
EVIDENCE=PR #27 / c8a71557 / merge 5520a66e / runs 36552829937, 36552888934, 36552968602
STATUS=CLOSED_PASS
NEXT=P11.6 bilingual documentation
STOP_REASON=P11.5 fully closed; proceed to next backlog item
```
