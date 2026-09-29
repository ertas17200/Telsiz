# Telsiz Academy — English Navigation

> This English page is navigation/translation only. It does not create or change legal permission, frequency entitlement, licence rights, or regulatory meaning.

Canonical Turkish document path: `academy/README.md`  
Canonical Turkish document: [README.md](README.md)

## Trust contract

Academy sits **on top of** the existing provenance chain; it never bypasses it:

```text
official/trusted source
  -> source registry
  -> grounded rule/data
  -> validator
  -> Academy presentation
```

- A `source_grounded` module may reference only registered/validated source and rule IDs.
- A legal-content module must remain bound to verified/current official legal authority and verified legal rules.
- An `educational_only` module cannot create a source-backed legal claim.
- Community references may inspire UX or educational tooling, but cannot establish permission to transmit in Türkiye.
- Academy modules keep `legal_verdicts=false`. Legal allow/deny decisions stay in the repository's fail-closed decision engine.

## Module navigation

- `ACADEMY.TR.CORE-COMPLIANCE` — Türkiye core compliance view
- `ACADEMY.TR.EXAM-OPERATIONS` — official operational exam/certificate source map
- `ACADEMY.IARU.BANDPLAN-PRACTICE` — IARU Region 1 operating-practice guidance
- `ACADEMY.TOOL.GRID-LOCATOR` — deterministic Maidenhead grid tool
- `ACADEMY.TOOL.MORSE-TRAINER` — ITU-grounded Morse trainer
- `ACADEMY.TOOL.QCODE-RST-TRAINER` — Q-code and RS(T) trainer
- `ACADEMY.TOOL.QSO-LOG-ADIF` — bounded QSO log / ADIF exporter
- `ACADEMY.TOOL.RF-WAVELENGTH` — source-grounded RF wavelength/electrical-length calculator
- `ACADEMY.DEVICE.YAESU.FTM400` — Yaesu FTM-400 manual/firmware compatibility guard
- `ACADEMY.TR.REPEATER-OPERATIONS` — Türkiye repeater operational snapshot with authority separation

## Underlying source IDs

The module navigation is tied to these canonical source IDs:

- `TR.BTK.FTM.TECH.2022-IK-SYD-245`
- `TR.KEGM.AMATEUR.FAQ`
- `IARU.R1.BANDPLANS`
- `ITU.R.M1677.1`
- `IARU.R1.EOP.4.2.0`
- `ITU.R.M1172.0`
- `IARU.R1.VHF.HANDBOOK.10.02`
- `ADIF.SPEC.3.1.7`
- `BIPM.SI.DEFINING_CONSTANTS`
- `YAESU.FTM400.PRODUCT.ARCHIVE`
- `YAESU.FTM400DRDE.FW.INFO.2020-12-22`
- `YAESU.FTM400XDRXDE.FW.INFO.2020-12-22`
- `TR.TRAC.REPEATER.LIST`
- `TR.BTK.RADIO.PROCEDURES`

## Underlying rule IDs

- `TR.AMATEUR.TECHNICAL_COMPLIANCE`
- `TR.AMATEUR.DUMMY_LOAD`
- `IARU.R1.NATIONAL_RULES_PREVAIL`

## Important authority boundary

The repeater module intentionally combines two **different roles** without merging their authority:

- `TR.TRAC.REPEATER.LIST` = association operational observations.
- `TR.BTK.RADIO.PROCEDURES` = official permission/licensing context.

A repeater shown as `Aktif` by TRAC is not automatically treated as officially permitted by BTK.

## Translation safety

This page is tracked by `docs/translations.json`.

The manifest pins the Git blob SHA-1 of `academy/README.md`. If the canonical Turkish Academy contract changes, the bilingual validator must fail until this page is reviewed. This prevents an English page from silently keeping an outdated legal/trust meaning.
