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

This source is registered as **official_technical**, not promoted to an atomic legal rule source in this layer. The underlying 2022 regulation remains a separate verification target.

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

## Known gap

The full consolidated text and amendment/provenance chain of the **Afet ve Acil Durum Müdahale Hizmetleri Yönetmeliği** is not yet promoted into the legal knowledge layer. It is tracked as:

`CAND.TR.AFAD.MUDAHALE_REGULATION.2022`

Until that source is independently verified, this layer must remain contextual/operational rather than legal.
