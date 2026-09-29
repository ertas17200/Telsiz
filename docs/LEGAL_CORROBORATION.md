# Official Legal Corroboration Layer

Canonical registry: `data/legal_corroborations.json`

## Purpose

The corroboration layer preserves useful statements from an official institution when the canonical consolidated legal text cannot yet be retrieved in the current verification path.

It is deliberately weaker than a canonical legal source.

```text
OFFICIAL CORROBORATION != CANONICAL CONSOLIDATED LAW
```

A corroboration record:

- does not become a `source_id`;
- cannot promote the canonical source to `verified`;
- cannot ground a verified legal rule;
- cannot ground a semantic frequency permission row;
- cannot emit a legal verdict;
- exists for provenance, cross-checking and later exact-text reconciliation.

## Current records

### Law No. 5809 — BTK FTM page

Canonical source:

`TR.BTK.EHK.5809`

Corroboration:

`TR.BTK.EHK.5809.CORR.FTM.2026-09-29`

Observed official BTK material covers:

- Article 37/3 — direct quotation observed on the BTK page;
- Article 40/1 — direct quotation observed on the BTK page;
- Article 36 — referenced in the exemption-compliance explanation;
- Article 63 — referenced in the enforcement explanation.

The canonical `TR.BTK.EHK.5809` record remains `pending`.

### Law No. 5809 — BTK installation/use page

Corroboration:

`TR.BTK.EHK.5809.CORR.INSTALL.2026-09-29`

Observed official BTK material includes direct quotations attributed to:

- Article 36/1-b;
- Article 37/1.

This second page is still not a substitute for the canonical consolidated law text.

### FTM Regulation — BTK FTM page

Canonical source:

`TR.BTK.FTM.REGULATION.2018`

Corroboration:

`TR.BTK.FTM.REGULATION.2018.CORR.BTK.2026-09-29`

Observed official BTK material includes:

- publication metadata: 27.11.2018 / Official Gazette 30608;
- a direct quotation attributed to Article 6/1 regarding publication of Technical Criteria.

The canonical regulation record remains `pending`.

## Validator

```bash
python scripts/validate_legal_corroborations.py
```

The validator enforces:

1. canonical source exists and is `official_legal`;
2. corroborating URL is HTTPS on `btk.gov.tr`;
3. `authority_scope=official_corroboration_only`;
4. `promotes_canonical_source=false`;
5. `may_ground_verified_legal_rule=false`;
6. `legal_verdicts=false`;
7. references have explicit article/evidence-kind/locator/summary;
8. corroboration IDs cannot overlap source IDs;
9. rules cannot cite corroboration IDs;
10. frequency rows cannot cite corroboration IDs.

## Promotion rule

A pending canonical legal source may be promoted only from the canonical/current legal artifact under the normal legal-source verification contract.

Official quotations on institutional explanatory pages are useful corroboration but **never sufficient by themselves** for canonical source promotion.

## Current status

```text
P1_CANONICAL_SOURCE=TR.BTK.EHK.5809
P1_CANONICAL_VERIFICATION=pending
P1_CORROBORATION=PASS
P1_RULE_PROMOTION=HOLD

P2_CANONICAL_SOURCE=TR.BTK.FTM.REGULATION.2018
P2_CANONICAL_VERIFICATION=pending
P2_CORROBORATION=PASS
P2_RULE_PROMOTION=HOLD
```
