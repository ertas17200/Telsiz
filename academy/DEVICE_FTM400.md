# Yaesu FTM-400 Device Manual / Firmware Guard

This module is the first P11.4 manufacturer-manual intake.

Supported model families:

- `FTM-400DR / FTM-400DE`
- `FTM-400XDR / FTM-400XDE`

## Why the families are separate

Yaesu's official firmware update notices explicitly state that DR/DE firmware is **not compatible** with XDR/XDE firmware, and vice versa. The repository therefore models them as mutually incompatible firmware families.

Documented 2020 targets:

| Family | MAIN | DSP |
|---|---:|---:|
| FTM-400DR/DE | 3.50 | 4.31 |
| FTM-400XDR/XDE | 4.50 | 4.31 |

These values are recorded as the targets in Yaesu's 22 Dec 2020 firmware information documents. The version checker does not infer whether an arbitrary different version is "older" or "newer"; a mismatch returns `VERIFY_BEFORE_UPDATE`.

## Destination is mandatory

The manufacturer documents provide distinct MAIN packages for:

- `USA`
- `AUS`
- `EXP` (the document describes this as EXP/EU/CHN)

Telsiz does **not** infer destination from the user's current country. For example, entering `EU` or `TURKEY` is rejected; the physical radio's manufacturer destination must be established and passed explicitly.

## Operating manuals

Official Yaesu links for both Operating Manuals were identified on the manufacturer product page, but the files exceeded the current full-content verification path's size limit. Their source records therefore remain:

`verification_status = pending`

No detailed operating-manual claim should be promoted from them until the full content is verified.

## Update procedure gate

This layer selects a documented package filename only. It does **not** provide the firmware-writing procedure.

Yaesu's firmware information documents instruct the user to read the separate Firmware Upgrade Manual contained with the firmware package. Until that package-specific manual is ingested and verified, results return:

`update_instruction_status = REQUIRE_PACKAGE_FIRMWARE_UPGRADE_MANUAL`

## Usage

```bash
python scripts/device_firmware_guard.py package FTM-400DR EXP
python scripts/device_firmware_guard.py versions FTM-400DR --main 3.50 --dsp 4.31
```

The output is technical device guidance only and always carries:

`"legal_verdict": null`
