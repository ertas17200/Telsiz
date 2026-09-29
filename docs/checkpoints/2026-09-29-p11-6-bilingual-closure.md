# P11.6 Bilingual Documentation Closure — 2026-09-29

## FOUND

The repository had source-grounded Turkish canonical documentation, but no CI-enforced mechanism prevented an English translation/navigation page from silently drifting after a canonical Turkish edit.

## ROOT_CAUSE

Plain translated Markdown does not carry machine-verifiable provenance. Without a binding between canonical and translated documents, later edits could leave English guidance stale or could accidentally change authority/legal meaning.

## SCOPE

P11.6 — bilingual documentation baseline.

This closure intentionally implements **English navigation**, not a second independent legal corpus.

## FIX

Added:

- `README_EN.md`
- `academy/README_EN.md`
- `docs/translations.json`
- `scripts/validate_translations.py`
- `tests/test_translations.py`
- CI step `Validate bilingual documentation`
- canonical English-navigation links from `README.md` and `academy/README.md`

The manifest binds each English navigation page to:

- canonical Turkish path;
- canonical Turkish Git blob SHA-1;
- the same verified source IDs;
- the same verified rule IDs;
- `legal_verdicts=false`;
- `canonical_controls=true`.

## FAIL-CLOSED CONTRACT

A canonical Turkish document change invalidates its stored blob pin and produces:

```text
RETRANSLATION_REQUIRED
```

English navigation is rejected if it:

- omits its canonical Turkish path;
- omits the translation-only disclaimer;
- omits the no-legal-permission disclaimer;
- references an unknown source/rule ID;
- promotes a pending/unverified source;
- attempts to enable `legal_verdicts=true`;
- omits a manifest-declared source/rule ID from the translated page.

Canonical Turkish/source-backed records control on disagreement.

## VALIDATION

Final feature branch head:

```text
HEAD=bebc284ec63ad7e21316743fcfd7d96e8609b711
```

Push exact-head evidence:

```text
PUSH_RUN=36553727434
PUSH_JOB=109357767692
PUSH_RUNNER=GitHub Actions 1000014169
PUSH_CI=completed/success
TRANSLATIONS=2/2
TESTS=246/246
EXACT_HEAD=PASS
WORKTREE=PASS
```

Pull-request exact-head evidence:

```text
PR=32
PR_RUN=36553802790
PR_JOB=109358013114
PR_RUNNER=GitHub Actions 1000014170
PR_CI=completed/success
TRANSLATION_GATE=PASS
ALL_STEPS=success
```

Negative translation tests explicitly cover:

- canonical blob drift -> retranslation required;
- legal verdict enablement rejection;
- pending-source promotion rejection;
- unknown-source rejection;
- canonical ID/disclaimer omission rejection.

## MERGE / MAIN EVIDENCE

PR #32 squash merge:

```text
MERGE_SHA=dec037601a1aacc255b25e50b7b2200d54c86ded
MAIN_RUN=36553951787
MAIN_JOB=109358504853
MAIN_RUNNER=GitHub Actions 1000014171
MAIN_CI=completed/success
MAIN_TESTS=246/246
TRANSLATIONS=2/2
FINAL_EXACT_HEAD=PASS
FINAL_WORKTREE=PASS
OPEN_PRS_AFTER_MERGE=0
```

## P0 REMAINS UNCHANGED

Bilingual documentation does not relax the official-source gate:

```text
FREQUENCY_COVERAGE=partial
BTK_ARTIFACT_STATUS=awaiting_bytes
BTK_ARTIFACT_SHA256=UNKNOWN
P0_SEMANTIC_PROMOTION=HOLD
```

The open BTK source conflicts remain unresolved and cannot be normalized by translation.

## STATUS

```text
FOUND=translation drift risk
ROOT_CAUSE=translations lacked canonical provenance binding
SCOPE=P11.6 bilingual navigation baseline
FIX=blob-pinned translation manifest + validator + negative tests + CI
VALIDATION=2/2 translations; 246/246 tests
CI=PASS on push, pull_request and post-merge main
EVIDENCE=PR #32 / bebc284e / merge dec03760 / runs 36553727434,36553802790,36553951787
STATUS=CLOSED_PASS
NEXT=inspect remaining P11 backlog; if none, return to highest-priority unresolved official-source gate
STOP_REASON=P11.6 completed
```
