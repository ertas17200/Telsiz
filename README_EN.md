# Telsiz — English Navigation

> This English page is navigation/translation only. It does not create or change legal permission, frequency entitlement, licence rights, or regulatory meaning.

Canonical Turkish document path: `README.md`  
Canonical Turkish document: [README.md](README.md)

## Purpose

Telsiz is a source-grounded AI knowledge base for amateur radio, initially focused on Türkiye. It separates two layers that must never be silently merged:

1. **Legal / official sources** — laws, regulations, official decisions, allocations and competent-authority publications.
2. **Amateur-radio / technical sources** — trusted associations, manuals, training material and established technical publications.

When the English navigation differs from the canonical Turkish/source records, the canonical Turkish/source-backed record controls.

## Quick start — ask Telsiz

```bash
python scripts/ask.py "C sınıfı belgeyle 145 MHz'te 10 W kullanabilir miyim?"
```

`scripts/ask.py` answers Turkish questions in the canonical answer format. Every sentence is traceable to a verified rule, source and page; questions that cannot be grounded are refused. It does not create legal permission: verdicts come from the fail-closed frequency decision engine. See [docs/ASK.md](docs/ASK.md) (Turkish).

## Authority order

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

A lower-authority source cannot create a Turkish legal permission or override a higher-authority source.

## Fail-closed status

The repository intentionally refuses to invent missing legal facts.

- The BTK amateur table has a validated 33-row raw transcription, but semantic coverage is still partial.
- The BTK PDF bytes are verified and SHA-256 bound (`data/artifacts.json`); semantic promotion of the raw rows is still partial.
- Open source-internal conflicts remain recorded.
- P1–P3 legal-source work remains subject to exact-text verification.
- TRAC repeater status is operational association information; it is not proof of BTK permission.

## Core source IDs

This navigation is explicitly tied to the same registered identifiers used by the Turkish/source-backed layer:

- `TR.BTK.FTM.TECH.2022-IK-SYD-245`
- `TR.BTK.RADIO.PROCEDURES`
- `TR.KEGM.AMATEUR.FAQ`
- `IARU.R1.BANDPLANS`
- `TR.TRAC.REPEATER.LIST`

## Core rule IDs

- `TR.AMATEUR.TECHNICAL_COMPLIANCE`
- `IARU.R1.NATIONAL_RULES_PREVAIL`

These identifiers are references to the machine-readable canonical registries; this English page is not an independent rule source.

## Navigation

### Repository policy and evidence

- [Current repository status](docs/REPO_STATUS.md)
- [Grounded answer engine (`ask.py`)](docs/ASK.md)
- [Project scope](docs/PROJECT_SCOPE.md)
- [Source policy](docs/SOURCE_POLICY.md)
- [AI answer policy](docs/AI_ANSWER_POLICY.md)
- [Grounding contract](docs/GROUNDING_CONTRACT.md)
- [Frequency-table contract](docs/FREQUENCY_TABLE.md)
- [Official-source access log](docs/SOURCE_ACCESS_LOG.md)
- [Known source conflicts](docs/SOURCE_CONFLICTS.md)
- [Unverified source candidates](docs/SOURCE_CANDIDATES.md)

### User-facing Academy

- [Academy English navigation](academy/README_EN.md)
- [Canonical Academy Turkish document](academy/README.md)
- [Grounded practice exam contract](academy/EXAM.md)
- [Grid Locator](academy/GRID_LOCATOR.md)
- [Morse Trainer](academy/MORSE_TRAINER.md)
- [Q-code / RS(T) Trainer](academy/QCODE_RST_TRAINER.md)
- [QSO log / ADIF exporter](academy/QSO_LOG_ADIF.md)
- [RF wavelength calculator](academy/RF_WAVELENGTH.md)
- [Yaesu FTM-400 device layer](academy/DEVICE_FTM400.md)
- [Türkiye repeater operational snapshot](academy/REPEATERS_TR.md)

## Translation safety

The bilingual layer is CI-gated by `docs/translations.json` and `scripts/validate_translations.py`.

The manifest pins the Git blob SHA-1 of the canonical Turkish document. If that Turkish document changes, CI must fail with a retranslation-required condition until the English navigation is reviewed and the pin is updated.

The translation layer never bypasses `data/sources.json`, `data/rules.json`, the frequency decision engine, or the source-authority hierarchy.
