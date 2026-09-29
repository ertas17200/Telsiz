# P0 scope + semantic-readiness integration closure — 2026-09-29

## FOUND

The repository had two valid but separately developed P0 advances: a 33/33 fail-closed frequency scope index and a 33/33 semantic-promotion readiness map. The semantic branch was created before the scope-index merge and therefore could not be merged on stale-base evidence.

## ROOT_CAUSE

Parallel main advancement made the original semantic PR base stale. Direct merge would have discarded the rule that stale-base CI is not merge evidence.

## FIX

- merged PR #37 first: 33/33 evidence-only frequency scope index;
- closed stale PR #38 as superseded;
- rebuilt the semantic delta on current main;
- preserved both CI gates in one workflow;
- merged current-main integration PR #39;
- kept P0 fail-closed and partial.

## VALIDATION

```text
PR39_HEAD=e8c058528111b935ac3ddfdbd8fc62aa99f49f43
PR39_RUN=36561833318
PR39_JOB=109384283287
PR39_RUNNER=GitHub Actions 1000014213
PR39_CI=PASS
PR39_TESTS=283/283

MERGE_SHA=c8bf5363a6732707fa279513521f0f47752d7833
MAIN_RUN=36561908930
MAIN_JOB=109384529383
MAIN_RUNNER=GitHub Actions 1000014214
MAIN_CI=PASS
MAIN_TESTS=283/283
```

## EVIDENCE

- raw BTK rows: 33/33
- frequency scope entries: 33/33
- semantic readiness rows: 33/33
- partial semantic mappings: 8
- rows not ready under current schema: 25
- canonical BTK artifact: verified bytes / unchanged
- open PRs after merge: 0

## FAIL-CLOSED BOUNDARIES

- scope lookup never emits ALLOWED;
- absence from the primary raw scope remains UNKNOWN, not prohibited;
- conditional B-class exceptions are not promoted to primary scope;
- 136 GHz shared boundary preserves both source rows;
- 50–52 MHz A/B 100 W is only a known general power limit;
- beacon-specific 25 W context remains separately unresolved;
- e.i.r.p. rows wait for a power-basis model;
- dual values such as 75 W / 400 W PEP wait for structured multivalue semantics;
- A3J/J2C and the 28 MHz unit anomaly remain explicit source conflicts.

## STATUS

```text
FOUND=parallel stale-base semantic work
FIX=current-main clean integration
VALIDATION=PASS
CI=PASS
GITHUB=PASS
P0_BYTE_BLOCKER=CLOSED
P0_SCOPE_INDEX=PASS
P0_READINESS_MAP=PASS
P0_SEMANTIC_COVERAGE=PARTIAL
P0=HOLD
NEXT=structured power/condition modeling + source-conflict resolution
STOP_REASON=none
```
