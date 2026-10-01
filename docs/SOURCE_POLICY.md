# Source Policy

## 1. Source classes

### A. official_legal

Primary legal or regulatory material published by a competent authority.

Examples include legislation, regulations, official decisions, official gazette material and legally operative public-authority publications.

### B. official_technical

Technical or administrative information published by a competent public authority that is not itself the operative legal text.

### C. amateur_association

Material published by a recognized amateur-radio association or club.

### D. technical_manual

Manufacturer, standards-oriented or technically authoritative equipment/protocol documentation.

### E. educational

Training material from identifiable institutions or established amateur-radio education sources.

### F. community

Forums, personal websites, social media, mailing lists and other community-generated material.

Community content is discovery material only unless independently corroborated.

## 2. Authority order

```
official_legal
    >
official_technical
    >
amateur_association
    >
technical_manual / educational
    >
community
```

The order expresses answer authority, not absolute correctness in every domain. A radio manufacturer manual may be the strongest source for a device-specific specification, while it cannot override a legal requirement.

## 3. Mandatory metadata

Every indexed source must include:

- unique source id;
- title;
- publisher;
- source type;
- jurisdiction;
- canonical URL;
- topic tags;
- verification status;
- verification timestamp;
- content hash when a captured artifact is stored.

Legal/regulatory records additionally require, where applicable:

- publication date;
- effective date;
- current/superseded/repealed/unknown status;
- legal instrument identifier;
- article/section reference;
- supersedes/superseded-by relationships.

## 4. Verification states

- `verified` — source origin and metadata checked.
- `pending` — candidate source awaiting review.
- `unverified` — insufficient evidence to rely on.
- `deprecated` — retained for history but not for current answers.

Only `verified` sources may support definitive current legal claims.

## 5. Conflict handling

When sources conflict:

1. identify the subject and jurisdiction;
2. compare authority level;
3. compare publication/effective dates;
4. check whether one source supersedes another;
5. preserve both records when historically useful;
6. present the conflict explicitly if it cannot be resolved.

Do not silently choose the more convenient statement.

## 6. AI grounding rule

For a legal/regulatory answer, an AI must be able to identify the source record used. If no verified legal source supports the answer, the response must be framed as unverified or require current-source verification.

## 7. Artifact archival

When an official artifact (e.g. a PDF) is fetched:

1. record `source_url`, fetch time, HTTP status, content type, size, page count and the raw-byte SHA-256;
2. store the SHA-256 in the source record's `content_sha256`;
3. do not commit the raw artifact unless its licence clearly permits it — metadata and hash are sufficient;
4. keep extracted structured data in GitHub and a human-readable provenance summary in the Drive knowledge base.

A new fetch of the same URL whose SHA-256 differs from the recorded value means `SOURCE_CHANGED`: the source and every rule/row derived from it return to `REVERIFY_REQUIRED` (not `verified`) until re-checked. A changed file is never silently treated as equivalent to the recorded one.

## 8. Candidate sources

Sources that are known to be needed but not yet verified live in `data/source_candidates.json` (human view: `docs/SOURCE_CANDIDATES.md`). A candidate never carries a canonical URL, never has a verified status and can never be cited by a rule or frequency row. On verification it is promoted to `data/sources.json` with real metadata and removed from the candidate file.

## 9. Open-source repository sources

Public repositories (e.g. GitHub) may be used as sources only under these conditions:

1. the exact commit is pinned, and every cited file carries its Git blob SHA-1 and SHA-256;
2. every value has a `path#Lnn` locator, and a validator can re-check the values against a clone of the pinned commit (`--verify-clone`);
3. the licence is recorded; share-alike licensed data is not copied into this repository without an explicit decision. When it is copied, the data file carries the attribution and change notice, stays under the same licence, drops personal contact data, and is listed in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md);
4. an independent implementation is a `community` source: it is labelled as such in every answer and never upgraded without corroboration from the protocol's authoritative publication;
5. mirrors of other projects are not used unless their authority is verified;
6. no open-source repository can create legal permission or a Turkish frequency entitlement.



## 10. Mutable community operational datasets

Crowdsourced or association-operated operational datasets (for example satellite transmitter databases or repeater snapshots) are handled as **mutable snapshots**, not legal authority.

Required controls:

1. record the source organisation, licence, observation timestamp and exact upstream page/API identifiers;
2. preserve the upstream object identifier where available;
3. do not infer legal permission, national frequency entitlement or licensing authority from the presence of a record;
4. unknown/missing records must stay unknown — no fuzzy or nearest-match invention;
5. distinguish stable identity fields from volatile operational status;
6. if upstream data are copied/adapted under a share-alike licence, keep attribution/change notices and the same licence on the adapted dataset;
7. keep legal decision logic isolated from the operational snapshot;
8. re-snapshot or independently corroborate before presenting volatile status as current.

For satellite data specifically, `SOURCE_LISTED` / a transmitter frequency means only that the technical source lists it. It does not mean an operator in Türkiye may transmit on that frequency.

## 11. Manufacturer drawings, images and datasheets

Manufacturer product drawings, photos, dimension sheets and PDFs are copyrighted by default.

1. they are not copied into this repository unless the manufacturer's licence or written permission allows it, and that permission is recorded with the source;
2. without such permission, only the source URL, retrieval date, byte hash and factual values (with page/figure locators) may be recorded;
3. factual values from a manufacturer are `technical_manual` claims about that product, not legal permission and not independent measurement;
4. diagrams drawn for Telsiz must be original work generated from Telsiz's own sourced formulas, and must not trace or reproduce a manufacturer drawing.
