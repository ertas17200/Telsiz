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
│   ├── FREQUENCY_TABLE.md
│   ├── GROUNDING_CONTRACT.md
│   ├── PROJECT_SCOPE.md
│   ├── REPO_STATUS.md
│   ├── SOURCE_ACCESS_LOG.md
│   ├── SOURCE_CONFLICTS.md
│   └── SOURCE_POLICY.md
├── schemas/
│   ├── rule.schema.json
│   └── source.schema.json
├── scripts/
│   ├── check_repo_hygiene.py
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
python scripts/check_repo_hygiene.py
python scripts/validate_knowledge.py
python -m unittest discover -s tests -p "test_*.py" -v
```

The same checks run in GitHub Actions.

## Source registry

The canonical registry is:

```text
data/sources.json
```

Do not add a source as `verified` until its publisher, canonical URL, status and verification metadata have actually been checked.

## Project documents

- [Current repository status](docs/REPO_STATUS.md)
- [Project scope](docs/PROJECT_SCOPE.md)
- [Source policy](docs/SOURCE_POLICY.md)
- [AI answer policy](docs/AI_ANSWER_POLICY.md)
- [Grounding contract](docs/GROUNDING_CONTRACT.md)
- [Frequency table contract](docs/FREQUENCY_TABLE.md)
- [Official source access log](docs/SOURCE_ACCESS_LOG.md)
- [Known source conflicts](docs/SOURCE_CONFLICTS.md)

## Status

Repository controls and CI are operational. The amateur frequency table is intentionally **partial** while the official BTK artifact is inaccessible from the current source-ingestion environment. P0–P3 remain fail-closed until the relevant official sources can be fetched and verified.

See [REPO_STATUS.md](docs/REPO_STATUS.md) for the exact baseline, CI evidence, blockers and next sequence.
