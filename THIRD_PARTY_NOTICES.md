# Third-party data notices

Most of this repository is original work. The files below contain data adapted from third-party sources and remain under those sources' licences.

## APRS device identification database

- File: `data/aprs_deviceid.json`
- Source: APRS device identification database, `tocalls.yaml`, maintained by Hessu, OH7LZB, for aprs.fi — https://github.com/aprsorg/aprs-deviceid @ `845e3f89d54402a9aa90e765e14c14b7e5710892`
- Licence: Creative Commons Attribution-ShareAlike 2.0 (CC BY-SA 2.0) — https://creativecommons.org/licenses/by-sa/2.0/
- Changes: converted from YAML to JSON; the `classes`, `tocalls`, `mice` and `micelegacy` indexes are kept; personal `contact` fields are removed; a source line locator is added to each entry.
- The adapted file is distributed under the same CC BY-SA 2.0 licence.

## Referenced but not copied

- `data/digital_modes.json` records protocol parameters with line locators into ft8_lib (MIT, https://github.com/kgoba/ft8_lib @ `9fec6ca39886edbf96f4f5e71edc76da5074e871`); no source code is copied.
- `data/ax25_parameters.json` records AX.25/HDLC/AFSK parameter values with line locators into Dire Wolf (GPL-2.0, https://github.com/wb2osz/direwolf @ `eda1383f5fa9d8ba3cb27f99db1d2c79494404c9`); no source code is copied. The FCS table is regenerated from the polynomial, not copied.
