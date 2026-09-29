# BTK Semantic Promotion Readiness

This layer sits between the 33-row raw BTK transcription and the decision-oriented semantic frequency table.

## Purpose

`data/btk_semantic_promotion.json` maps every raw source row exactly once and records which fields can be promoted without inventing semantics.

It is **not** a permission table.

## Current state

- raw source rows mapped: **33/33**
- partial semantic mappings present after this change: **8**
- rows not ready for the current semantic schema: **25**
- canonical byte artifact: **verified and SHA-256 bound**
- frequency-table coverage: **partial**

The map keeps these categories distinct:

- exact frequency range and licence-class identity;
- power values that are directly representable as transmitter output;
- e.i.r.p. values that need a power-basis model;
- dual values such as `75 W, 400 W (PEP)` that need a multivalue/PEP model;
- emissions blocked by the `A3J/J2C` source conflict;
- free-text conditions that still require structured condition modeling.

## First new limited promotion

Raw source row 17 is visually explicit:

- 50–52 MHz
- A and B classes
- 100 W

Those three fields are promoted to:

`TR.FTM.AMATEUR.ROW.AB.50-52`

The same source row also carries EME/beacon context and inherits an emission cell containing the unresolved `A3J/J2C` anomaly. Therefore these semantic fields remain `null = NOT_EXTRACTED`:

- emission / bandwidth;
- station/use context;
- satellite / repeater / beacon / emergency flags;
- footnotes / special conditions.

A request within 100 W therefore remains `UNKNOWN` on the partial table. A request above the verified 100 W general row limit may be rejected as exceeding a known limit, while beacon-specific evaluation remains unresolved until the 25 W condition is modeled separately.

## Open source conflicts

- `TR-BTK-NUMBERING-001`
- `TR-BTK-EMISSION-001`
- `TR-BTK-UNIT-001`

No conflict is normalized or silently corrected.
