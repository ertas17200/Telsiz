---
applyTo: ".github/workflows/**,**/ci/**,**/*workflow*,**/*pipeline*"
---
# CI and exact HEAD
- Read existing workflows and runner constraints before editing. Preserve pinned actions and least-privilege permissions.
- Verify expected SHA, checked-out SHA and workflow run head SHA are identical.
- Count actual runner steps and check job conclusion. queued, pending, in_progress, skipped, cancelled, failure, runner=null, steps=0 and wrong-head are never PASS.
- Run targeted tests, regression and security checks; keep required failure gates fail closed.
- Log workflow run/job IDs, tested SHA, artifact integrity and any missing evidence to the PR/issue; never equate green CI with production trust acceptance.
