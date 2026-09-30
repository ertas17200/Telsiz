# Third-party data notices

Most of this repository is original work. The files below contain data adapted from third-party sources and remain under those sources' licences.

## APRS device identification database

- File: `data/aprs_deviceid.json`
- Source: APRS device identification database, `tocalls.yaml`, maintained by Hessu, OH7LZB, for aprs.fi — https://github.com/aprsorg/aprs-deviceid @ `845e3f89d54402a9aa90e765e14c14b7e5710892`
- Licence: Creative Commons Attribution-ShareAlike 2.0 (CC BY-SA 2.0) — https://creativecommons.org/licenses/by-sa/2.0/
- Changes: converted from YAML to JSON; the `classes`, `tocalls`, `mice` and `micelegacy` indexes are kept; personal `contact` fields are removed; a source line locator is added to each entry.
- The adapted file is distributed under the same CC BY-SA 2.0 licence.

## Referenced but not copied

- `data/radio_noise.json` records man-made and galactic noise coefficients with line locators into the ITU-R SG3 ITU-R-HF repository (https://github.com/ITU-R-Study-Group-3/ITU-R-HF @ `82017594a1c6cacfaa7e86954c4ae7b3a5825a3d`), whose README states the software may be used "free from any copyright assertions"; no source code is copied.

- `data/digital_modes.json` records protocol parameters with line locators into ft8_lib (MIT, https://github.com/kgoba/ft8_lib @ `9fec6ca39886edbf96f4f5e71edc76da5074e871`); no source code is copied.
- `data/ax25_parameters.json` records AX.25/HDLC/AFSK parameter values with line locators into Dire Wolf (GPL-2.0, https://github.com/wb2osz/direwolf @ `eda1383f5fa9d8ba3cb27f99db1d2c79494404c9`); no source code is copied. The FCS table is regenerated from the polynomial, not copied.
- `data/digital_voice.json` records DMR / D-STAR / System Fusion frame parameter values with line locators into MMDVMHost (GPL-2.0, https://github.com/g4klx/MMDVMHost @ `590c531391dfd3146073afbc3956f70d42c62a46`); no source code is copied.


## SatNOGS satellite/transmitter snapshot

- File: `data/satellite_transmitters.json`
- Source: SatNOGS DB, maintained by Libre Space Foundation and SatNOGS DB contributors — https://db.satnogs.org/
- Source licence: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) — https://creativecommons.org/licenses/by-sa/4.0/
- Source licence statement: https://db.satnogs.org/about/
- Changes: curated subset of ISS, SO-50, AO-73 and AO-91; selected transmitter/transponder fields normalized to JSON; frequencies normalized to Hz; source page URLs and SatNOGS transmitter UUIDs retained; contributor/contact fields and TLE/orbital data omitted.
- The adapted snapshot is distributed under the same CC BY-SA 4.0 licence.
- This dataset is technical/community information only and cannot establish legal permission, Turkish frequency entitlement, licensing authority or regulatory compliance.
