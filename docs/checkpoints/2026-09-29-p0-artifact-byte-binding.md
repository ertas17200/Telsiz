# P0 BTK byte-artifact binding checkpoint — 2026-09-29

## FOUND

The canonical BTK PDF remained reachable through the registered URL:

`https://www.btk.gov.tr/uploads/pages/ftm-teknik-olcutler-ek-5.pdf`

The conversation runtime could render the PDF but could not download raw bytes. A dedicated GitHub Actions observation was therefore used rather than treating renderer access as byte evidence.

## BUILD

Added a review-only canonical artifact fetcher with:

- registered-source-only URL selection;
- HTTPS enforcement;
- same-origin redirect enforcement;
- HTTP MIME enforcement;
- bounded streaming download;
- reuse of the existing PDF signature/size/SHA-256 gate;
- no automatic source/artifact mutation.

## PROBE EVIDENCE

```text
HEAD=5472204e5f9fcf9beee5219c724814259cbee42c
KNOWLEDGE_RUN=36559259428
KNOWLEDGE_JOB=109375881490
KNOWLEDGE_RESULT=success
TESTS=254/254

ARTIFACT_RUN=36559259435
ARTIFACT_JOB=109375881365
ARTIFACT_RESULT=success
RUNNER=GitHub Actions 1000014181
FETCHED_AT=2026-09-29T11:02:27Z
SIZE_BYTES=508766
SHA256=eff832fc30df1adf60e4a8c514a6069154d526d3ab88ae803b51a5536d103db0
FINAL_URL=https://www.btk.gov.tr/uploads/pages/ftm-teknik-olcutler-ek-5.pdf
INITIAL_CHANGE_STATUS=HASH_OBSERVED_BIND_REQUIRED
```

## BIND DECISION

The first observation was explicitly reviewed. The digest is bound to source `TR.BTK.FTM.TECH.2022-IK-SYD-245`, and the artifact record becomes:

```text
artifact_status=verified_bytes
change_status=UNCHANGED
reverify_required=false
```

This closes only the byte-artifact blocker. Semantic promotion remains fail-closed pending source-conflict handling.
