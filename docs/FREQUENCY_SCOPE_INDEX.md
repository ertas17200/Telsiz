# BTK Frequency Scope Index

`data/frequency_scope.json` is a **semantic scope-evidence layer**, not a permission table.

It maps all 33 visible rows of the verified BTK amateur table one-to-one into a machine-queryable class/frequency index while preserving the original row boundaries, class lists, power text, restrictions, source locator and known conflict IDs.

## Contract

A match means only:

> the requested licence class and frequency appear together in a primary visible BTK table row.

It does **not** mean:

- transmission is legally allowed;
- a requested emission is allowed;
- a requested power is allowed;
- repeater/satellite/beacon use is allowed;
- a conditional exception applies.

Every query returns `legal_status=UNKNOWN`. Legal decisions remain delegated to `scripts/frequency_lookup.py` and its verified semantic constraints.

## Why separate this from frequency_table.json?

`data/frequency_table.json` contains decision-relevant atomic constraints. Adding broad, incomplete rows there could overlap a narrower verified constraint and accidentally weaken a denial. For example, a generic 144–146 MHz C-class row with unknown power must not dilute the existing verified 5 W C-class limit.

The scope index therefore carries:

```text
decision_authority=scope_evidence_only
permission_inference=PROHIBITED
```

## Conditional B-class exceptions

The BTK raw source includes special training/promotion conditions for B-class operation inside rows whose primary class column is A.

Those conditions are **not promoted into the primary scope index**:

- 7000–7100 kHz training/promotion condition;
- the 28 MHz training/promotion condition whose source text also carries `TR-BTK-UNIT-001`.

They remain restriction/condition evidence and require separate atomic modeling.

## Query

```bash
python scripts/frequency_scope_lookup.py --class C --frequency 145
```

Example shape:

```json
{
  "scope_status": "SOURCE_LISTED",
  "legal_status": "UNKNOWN",
  "permission_inference": "PROHIBITED"
}
```

## Validation

```bash
python scripts/validate_frequency_scope.py
```

The validator requires:

- exactly 33 scope entries;
- exact row-index sequence 1–33;
- exact raw-row frequency, unit, class, power-text, restrictions and locator equality;
- no promotion of conditional B-class exceptions into the primary class column;
- explicit mapping of emission/unit source conflicts;
- evidence-only authority on every entry.

## Status

```text
RAW_ROWS=33
SCOPE_ENTRIES=33
SCOPE_COVERAGE=complete_raw_scope_index
LEGAL_VERDICT_FROM_SCOPE=DISABLED
DECISION_TABLE_COVERAGE=partial
```
