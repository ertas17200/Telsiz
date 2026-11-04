# Repository Agent Execution Rules

Read `.github/copilot-instructions.md` and applicable `.github/instructions/*.instructions.md` before making changes. Existing repository policies and narrower directory instructions remain authoritative; do not override them.

Follow INSPECT -> PLAN -> CHANGE -> TARGETED TEST -> CI VERIFY -> EVIDENCE -> CLOSE -> NEXT -> RECHECK. Capture initial/final branch and exact HEAD; preserve user changes and avoid destructive Git operations.

Make minimal changes, run real checks, verify evidence and exact-head runner jobs, and record GitHub PR/issue audit links. Never claim PASS for skipped, queued, failed, wrong-head or missing-evidence jobs. Distinguish local success from ecosystem acceptance; unresolved mandatory proof is BLOCKED.

Never commit secrets or fabricate artifacts, SHA-256, authority receipts, or production PASS.
