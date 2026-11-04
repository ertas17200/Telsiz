---
applyTo: "**/*"
---
# Evidence and integrity
- Inspect repository and existing instructions before edits; establish branch, HEAD, working tree and baseline.
- Distinguish OBSERVED, VERIFIED, INFERRED, UNKNOWN and BLOCKED. Never infer PASS from file existence.
- For BOSS trust chains, verify SOURCE -> CANONICAL SOURCE -> CAPTURE -> SHA-256 -> MANIFEST -> VALIDATOR -> INDEPENDENT READBACK -> CI -> EXACT HEAD.
- Hash actual artifact bytes, compare recorded digests and verify references; never synthesize provenance, hashes, signatures or receipts.
- Missing or stale evidence must fail closed. Preserve audit trails and publish links to independently readable evidence.
