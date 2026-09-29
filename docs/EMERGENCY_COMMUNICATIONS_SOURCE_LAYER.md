# Emergency Communications Source Layer

## Purpose

This layer lets Telsiz answer basic disaster/emergency communications questions while keeping three different concepts separate:

1. **official disaster-response coordination** — AFAD / TAMP context;
2. **amateur operating practice** — IARU Region 1 training guidance;
3. **legal permission to transmit** — only the existing verified legal layer may decide this.

The emergency layer itself never grants frequency or transmit permission.

## Verified sources

### TR.AFAD.TAMP.2022

AFAD's official Türkiye Afet Müdahale Planı page is used for response-planning context. The page states that TAMP defines roles/responsibilities of disaster groups and coordination units, covers institutions, private sector, NGOs and natural persons, was updated/published on 15 September 2022 in Official Gazette no. 31954, and describes S1–S4 response levels.

This source is registered as **official_technical**, not promoted to an atomic legal rule source in this layer. Its legal-basis paragraph is now explicitly treated as **stale metadata**: the page still points to the 2022/5211 regulation, while the current regulation is 31.12.2025/10809.

### IARU.R1.EMCOMM.PROCEDURES

IARU Region 1's Emergency Operating Procedures page is used only for amateur training/operating practice. It says the emergency telecommunications guide exists to train radio amateurs, emphasizes fast and accurate message handling, notes local procedural differences, and explicitly acknowledges that its HF procedure is not as current as some groups would prefer.

It cannot create Turkish legal permission or official assignment.

## Machine-enforced boundaries

```text
legal_permission_from_this_layer=PROHIBITED
frequency_inference=PROHIBITED
amateur_status_implies_official_assignment=false
emergency_context_expands_transmit_permission=false
```

Therefore:

- “afet var” does **not** make an otherwise unsupported frequency legal;
- an amateur licence does **not** prove TAMP assignment;
- no universal Turkish “emergency frequency” is invented by this dataset;
- IARU practice never overrides BTK/other competent Turkish authority;
- the AFAD summary page is not substituted for the full consolidated regulation.

## Supported questions

Examples:

```bash
python scripts/emergency_comms.py "TAMP S3 ne demek?"
python scripts/emergency_comms.py "Afet frekansı hangisi?"
python scripts/ask.py "TAMP nedir ve afet haberleşmesinde ne ifade eder?"
python scripts/ask.py "Afet durumunda 145.500 MHz otomatik olarak serbest mi?"
```

The last example intentionally combines this emergency context with the existing BTK frequency engine. The emergency layer cannot turn UNKNOWN/NOT_ALLOWED legal evidence into permission.

## Current-law verification status

The former 24.02.2022 / 5211 regulation is no longer current. It is retained only as a verified historical source:

`TR.AFAD.MUDAHALE.REGULATION.2022-5211`

The current instrument is:

`TR.AFAD.MUDAHALE.REGULATION.2025-10809`

Currentness/provenance metadata is independently corroborated, and the exact Official Gazette PDF URL is resolved. However, the origin PDF body/raw bytes were not retrievable in the present verification environment. Therefore the current source remains `verification_status=pending`, and exact-text legal-rule promotion remains disabled.

The origin-fetch target is tracked as:

`CAND.TR.RG.AFAD.MUDAHALE.REGULATION.2025-10809`

Important consequence: the AFAD TAMP page's 2022/5211 legal-basis line must not be cited as the current legal basis. The emergency layer remains fail-closed until the current 10809 origin text is fetched and verified.
