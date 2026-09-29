# BTK Amateur Table Raw Extraction — 2026-09-28

## Scope

Official source:

- Source ID: `TR.BTK.FTM.TECH.2022-IK-SYD-245`
- Instrument: `2022/İK-SYD/245`
- Article: `MADDE 22`
- Canonical URL: `https://www.btk.gov.tr/uploads/pages/ftm-teknik-olcutler-ek-5.pdf`
- PDF pages: 47
- Amateur table: PDF pages 41-45/47
- Emission reference: PDF page 46/47

## Evidence method

The official BTK PDF was opened through a trusted PDF-rendering path that exposed both its text layer and page images. Pages containing Article 22, the amateur frequency table and Tablo 26-1 were visually checked.

A later dedicated GitHub Actions byte observation fetched the same registered canonical HTTPS URL. The reviewed baseline is **508766 bytes** with SHA-256 `eff832fc30df1adf60e4a8c514a6069154d526d3ab88ae803b51a5536d103db0` (run `36559259435`, job `109375881365`, fetched `2026-09-29T11:02:27Z`). The digest is now explicitly bound in the source and artifact registries.

## Result

`data/btk_amateur_table_raw.json` contains **33** visible source frequency rows.

`data/btk_emission_types.json` contains **24** Tablo 26-1 emission definitions with their displayed bandwidth values.

The raw layer records merged-cell inheritance explicitly because several power/emission/class cells visually span multiple frequency rows and page breaks.

## Key verified source facts

- Article 22 says amateur stations are used subject to the technical criteria in the referenced table.
- A-class operators use frequencies permitted to their class under the table.
- B/C operators may use all amateur bands/emissions under the supervision/responsibility conditions stated in Article 22(10); otherwise they are restricted to their own class permissions.
- The table visibly includes C class in 144-146 MHz and the 430 MHz sub-band group; the source restriction text states a 5 W transmitter-output limit for C class in 144-146 MHz and 430-440 MHz.
- Repeater-only sub-bands are visibly identified at 431.550-431.825 MHz and 439.150-439.425 MHz.
- Tablo 26-1 defines 24 emission codes; the 28 MHz-and-above table cell additionally shows J2C, which is not defined there.

## Fail-closed status

```text
RAW_SOURCE_ROWS=33
RAW_ROW_TRANSCRIPTION=PASS
EMISSION_DEFINITIONS=24
ARTIFACT_STATUS=verified_bytes
ARTIFACT_SIZE_BYTES=508766
ARTIFACT_SHA256=eff832fc30df1adf60e4a8c514a6069154d526d3ab88ae803b51a5536d103db0
SEMANTIC_PROMOTION=HOLD_SOURCE_CONFLICTS_AND_SEMANTIC_MODEL
FREQUENCY_TABLE_COVERAGE=PARTIAL
```

No raw row is allowed to bypass `data/frequency_table.json` and directly create an `ALLOWED` legal verdict.

## Required next evidence

The byte-artifact gate is closed. The remaining P0 work is semantic and conflict-aware:

- keep all 33 raw rows mapped in `data/btk_semantic_promotion.json`;
- model e.i.r.p. separately from transmitter output power;
- model dual/PEP power values without flattening them;
- keep `A3J`/`J2C` blocked until the source conflict is resolved;
- structure beacon/EME/emergency/repeater and sub-range conditions before they can affect verdicts;
- preserve the 28 MHz source unit conflict without silent correction;
- keep `coverage_status=partial` until all completeness gates are satisfied.
