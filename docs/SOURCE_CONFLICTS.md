# Source Conflicts and Discrepancies

This file records source inconsistencies that an AI must not silently normalize.

## TR-BTK-NUMBERING-001

**Status:** OPEN  
**Detected:** 2026-09-28  
**Sources:**
- `TR.BTK.AMATEUR_OVERVIEW`
- `TR.BTK.FTM.TECH.2022-IK-SYD-245`

**Observation:** BTK's amateur-radio overview page refers to Article 21 of the Technical Criteria, while the currently served 2022/İK-SYD/245 PDF displays "Amatör telsiz istasyonu" as Article 22.

**Additional observation:** Article 22 refers to Table 26, while the immediately following table is visibly titled Table 25 in the PDF.

**Resolution policy:** Do not invent a corrected number. For exact legal/technical citation, use the current official PDF text and disclose the numbering inconsistency when relevant. Investigate amendment/version history before closing this record.


## TR-BTK-EMISSION-001

**Status:** OPEN  
**Detected:** 2026-09-28  
**Source:** `TR.BTK.FTM.TECH.2022-IK-SYD-245`

**Observation:** In the visually merged emission cell used by the 28 MHz-and-above rows, `F2B` appears twice and `J2C` is listed. In the immediately following `Tablo 26-1 Emisyon tipleri`, `J2C` has no definition, while `J3C` is defined.

**Resolution policy:** Preserve the source text as-is in the raw transcription, de-duplicate only the repeated `F2B` token for machine readability, keep `J2C` explicitly flagged as undefined, and do not silently replace it with `J3C`.

## TR-BTK-UNIT-001

**Status:** OPEN  
**Detected:** 2026-09-28  
**Source:** `TR.BTK.FTM.TECH.2022-IK-SYD-245`

**Observation:** The 28 MHz/HF row itself is `28000-29700 kHz`, but the B-class training/promotion sentence inside the restriction cell writes `28000-29700 MHz`.

**Resolution policy:** Preserve both values exactly in provenance. Do not normalize the sentence to kHz without amendment/version evidence. The semantic layer must remain fail-closed for this conditional permission until the discrepancy is resolved.
