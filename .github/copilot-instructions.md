# BOSS Autonomous Development & Verification Protocol

This repository follows a strict, fail-closed autonomous engineering lifecycle. Do not skip stages and do not mark work complete without programmatic evidence.

## Mandatory 9-Stage Lifecycle

1. **BUILD**
   - Implement the requested feature/fix with minimal, focused edits.
   - Follow the repository's existing architecture, patterns, naming, and style.
   - Do not introduce unused dependencies, dead code, or unrelated changes.

2. **CHECK**
   - Self-review for correctness, edge cases, performance, security, and backward compatibility.
   - Discover and run the repository's native lint, formatting, type-check, security, and static-analysis commands.
   - Fix every linter error and type mismatch before continuing.

3. **TEST**
   - Add or update unit, integration, and end-to-end tests for modified behavior.
   - Run targeted tests first, then the applicable local suite.
   - Gate: zero test failures.

4. **VERIFY CI**
   - Inspect CI/CD configuration and the exact commit/HEAD being validated.
   - Trigger or verify the applicable remote CI pipeline.
   - Gate: all required checks must be green on the exact expected HEAD.

5. **PROVE**
   - Capture concrete evidence: raw test output, build logs, CI job/step status, runner identity, relevant metrics, and exact commit SHA.
   - Evidence must be reproducible and sufficient to independently verify the result.

6. **GITHUB LOG**
   - Use an atomic Conventional Commit (for example: feat:, fix:, refactor:, test:, docs:, ci:).
   - Push the exact commit.
   - Post a structured Issue/PR update containing stage, status, proof, and commit SHA.

7. **CLOSE**
   - Verify every acceptance criterion is fulfilled.
   - Close the Issue/Task or mark the Pull Request Ready for Review only after all gates pass.

8. **NEXT**
   - Select the highest-priority actionable backlog item.
   - Start it in a dedicated branch/context.
   - Never mix unrelated issues in the same cycle.

9. **RECHECK**
   - After merge/integration, run the full applicable integration/regression suite on the canonical main/development branch.
   - Confirm there are no regressions, breaking changes, or silent failures.

## Fail-Fast Loopback

If **CHECK**, **TEST**, or **VERIFY CI** fails, immediately return to **BUILD**, fix the cause, and repeat the gates. Do not log a false PASS and do not close the task.

## Fail-Closed Rules

The following are **NOT PASS**:
- queued
- pending
- waiting
- requested
- in_progress
- skipped
- cancelled
- failure / failed
- timed_out
- wrong-head
- stale evidence
- SHA mismatch
- blank runner_name
- empty steps
- missing evidence
- unknown / unverified

Visual inspection alone is never sufficient for closure.

## Strict Isolation

Work on exactly one issue/feature per execution cycle. Preserve unrelated dirty work and never overwrite or discard user changes.

## Repository-Native Commands First

Before inventing commands, inspect the repository for its own tooling and instructions, including:
- package.json scripts
- pyproject.toml / requirements files
- Makefile / Taskfile
- PowerShell or shell automation
- test configuration
- lint/type-check configuration
- .github/workflows
- repository documentation and local agent instructions

Repository-specific commands and constraints take precedence over generic defaults, provided they do not weaken these verification gates.

## Required Status Record

Use this operational status shape when reporting development work:

FOUND / ROOT_CAUSE / SCOPE / BUILD / CHECK / TEST / CI / PROOF / GITHUB_LOG / CLOSE / NEXT / RECHECK / STATUS / STOP_REASON

Canonical loop:

**INSPECT → PLAN → CHANGE → TARGETED TEST → CI VERIFY → EVIDENCE → CLOSE → NEXT → RECHECK**

Turkish operator loop:

**YAP → KONTROL ET → TEST ET → CI DOĞRULA → KANITLA → KAPAT → NEXT → RECHECK**
