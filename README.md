# Telsiz

Source-grounded AI knowledge base for amateur radio, initially focused on Türkiye.

## Goal

When an amateur-radio operator asks an AI a question, the answer should be grounded in traceable information from two clearly separated layers:

1. **Legal / official sources** — current laws, regulations, official decisions, allocations and competent-authority publications.
2. **Amateur-radio / technical sources** — trusted associations, manuals, training material and established technical publications.

The project deliberately separates **what is legally required** from **what amateurs commonly do in practice**.

## Trust order

```text
OFFICIAL LEGAL
    >
OFFICIAL TECHNICAL
    >
TRUSTED AMATEUR ASSOCIATION
    >
TECHNICAL / EDUCATIONAL PUBLICATION
    >
COMMUNITY
```

A lower-authority source must not silently override a higher-authority source.

## Current repository structure

```text
Telsiz/
├── .github/workflows/
│   └── knowledge-validation.yml
├── data/
│   ├── frequency_table.json
│   ├── rules.json
│   └── sources.json
├── docs/
│   ├── AI_ANSWER_POLICY.md
│   ├── PROJECT_SCOPE.md
│   └── SOURCE_POLICY.md
├── schemas/
│   └── source.schema.json
├── scripts/
│   ├── frequency_lookup.py
│   └── validate_knowledge.py
└── tests/
```

## Fail-closed rule

Definitive legal/regulatory claims must be backed by a **verified** official source record.

If a source is missing, outdated, conflicting or not verified, the AI must say so instead of inventing an answer.

## Validation

Run:

```bash
python scripts/validate_knowledge.py
```

The same validation runs in GitHub Actions.

## Source registry

The canonical registry is:

```text
data/sources.json
```

Do not add a source as `verified` until its publisher, canonical URL, status and verification metadata have actually been checked.

## Project documents

- [Project scope](docs/PROJECT_SCOPE.md)
- [Source policy](docs/SOURCE_POLICY.md)
- [AI answer policy](docs/AI_ANSWER_POLICY.md)
- [Frequency table contract](docs/FREQUENCY_TABLE.md)

## Status

Bootstrap phase. The repository structure and validation contract are being established before authoritative source ingestion begins.
