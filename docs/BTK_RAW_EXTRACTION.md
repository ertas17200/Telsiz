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

The raw byte artifact itself could not be materialized into the code-execution runtime, so **no SHA-256 is claimed**.

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
ARTIFACT_SHA256=UNKNOWN
SEMANTIC_PROMOTION=HOLD
FREQUENCY_TABLE_COVERAGE=PARTIAL
```

No raw row is allowed to bypass `data/frequency_table.json` and directly create an `ALLOWED` legal verdict.

## Required next evidence

The remaining P0 artifact gate is byte-level acquisition of the same canonical official PDF, followed by:

- file size;
- SHA-256;
- source-registry hash binding;
- source-change detection;
- semantic normalization and conflict-aware mapping;
- exact-head CI and main CI.
