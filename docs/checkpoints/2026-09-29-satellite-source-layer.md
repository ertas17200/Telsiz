# Satellite source layer closure — 2026-09-29

## FOUND

The knowledge coverage map had no grounded satellite transmitter/transponder source layer.

## ROOT_CAUSE

Satellite operating data are dynamic and community-maintained, while Telsiz previously prioritized legal/frequency and core operator tooling. Mixing a mutable community satellite database directly into the legal decision engine would violate the authority hierarchy.

## SCOPE

Curated technical snapshot only:

- ISS / RS0ISS APRS
- SO-50 FM voice
- AO-73 linear transponder + BPSK telemetry
- AO-91 FM voice

## FIX

- registered `SATNOGS.DB.SATELLITE_TRANSMITTERS` as verified community technical source;
- added `data/satellite_transmitters.json` with 4 satellites and 5 selected transmitter/transponder records;
- preserved SatNOGS UUIDs, source pages and observation timestamp;
- added CC BY-SA 4.0 attribution/share-alike notice;
- added deterministic validator and exact-match lookup;
- routed satellite questions through `ask.py`;
- added negative tests so unknown aliases are not guessed;
- added CI gate `Validate satellite transmitter snapshot`.

## VALIDATION

```text
PUSH_HEAD=5915cc35b518eea53f9fe383611ab7b544d28078
PUSH_RUN=36596442950
PUSH_JOB=109502455206
PUSH_RUNNER=GitHub Actions 1000014242
PUSH_CI=PASS

PR=48
PR_RUN=36596776703
PR_JOB=109503606930
PR_RUNNER=GitHub Actions 1000014243
PR_CI=PASS
PR_TESTS=404/404

MERGE_SHA=609a08b214a41e5b060f7e70ae922df92ab8562b
MAIN_RUN=36596842015
MAIN_JOB=109503835319
MAIN_RUNNER=GitHub Actions 1000014244
MAIN_CI=PASS
MAIN_TESTS=404/404
```

## SOURCE / LICENCE EVIDENCE

```text
SOURCE_ID=SATNOGS.DB.SATELLITE_TRANSMITTERS
PUBLISHER=Libre Space Foundation / SatNOGS DB contributors
SOURCE_TYPE=community
LICENSE=CC-BY-SA-4.0
ADAPTED_DATA=data/satellite_transmitters.json
SATELLITES=4
SELECTED_RECORDS=5
TLE_DATA_COPIED=no
CONTACT_FIELDS_COPIED=no
```

## FAIL-CLOSED BOUNDARIES

- legal_status remains UNKNOWN;
- permission_inference remains PROHIBITED;
- listed satellite uplink/downlink is not Turkish transmit permission;
- absence from this curated subset is not prohibition/nonexistence;
- exact alias/NORAD matching only;
- operational status is mutable and needs upstream freshness verification;
- community satellite data cannot override official legal sources.

## STATUS

```text
FOUND=ungrounded satellite knowledge gap
FIX=source-grounded SatNOGS technical snapshot
VALIDATION=PASS
CI=PASS
GITHUB=PASS
SATELLITE_LAYER=PASS
LEGAL_AUTHORITY_FROM_SATELLITE_DATA=DISABLED
NEXT=controlled satellite expansion or emergency-communications source layer
STOP_REASON=none
```
