---
applyTo: "**/tests/**,**/test_*,**/*_test.*,**/*.spec.*,**/schemas/**,**/validators/**"
---
# Testing and regression
- Reproduce the issue and establish baseline before changes; make minimal safe diffs.
- Execute relevant unit, integration, schema, lint, build and regression checks where supported.
- Test negative cases: missing/duplicate/stale artifacts, malformed input, wrong SHA, wrong HEAD, zero tests and skipped required checks.
- Never delete or weaken a test to force green. Record exact commands, counts, failures and blocked checks.
- Review final diff and protect public interfaces, manifests and dependency locks.
