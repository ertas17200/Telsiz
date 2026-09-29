# Satellite Source Layer

## Purpose

This layer gives Telsiz a small, source-grounded amateur-satellite knowledge surface without mixing operational satellite data into the Turkish legal permission engine.

Canonical data:

- `data/satellite_transmitters.json`
- source record: `SATNOGS.DB.SATELLITE_TRANSMITTERS`
- validator: `scripts/validate_satellites.py`
- lookup: `scripts/satellite_lookup.py`

## Source and licence

SatNOGS DB is maintained by Libre Space Foundation with community contributions. Its About page states that SatNOGS DB data are public and distributed under **CC BY-SA 4.0**.

The adapted Telsiz snapshot is therefore also treated as CC BY-SA 4.0 data, with attribution and modification notes in `THIRD_PARTY_NOTICES.md`.

## Curated v1 snapshot

The first snapshot intentionally contains only four widely useful amateur-relevant objects and five selected transmitter/transponder records:

| Satellite | NORAD | Selected record |
|---|---:|---|
| ISS | 25544 | Mode V APRS — 145.825 MHz AFSK, 1200 baud, uplink/downlink |
| SO-50 / SAUDISAT 1C | 27607 | FM voice — 145.850 MHz uplink, 436.795 MHz downlink, CTCSS 67 Hz |
| AO-73 / FUNCUBE-1 | 39444 | U/V inverting linear transponder + 145.935 MHz BPSK telemetry |
| AO-91 / FOX-1B | 43017 | FM voice — 435.250 MHz uplink, 145.960 MHz downlink; source says no CTCSS |

This is a curated technical snapshot, not a full SatNOGS mirror.

## Fail-closed contract

Every lookup returns:

```text
legal_status=UNKNOWN
permission_inference=PROHIBITED
decision_authority=technical_reference_only
```

Meaning:

- a listed uplink does not create permission to transmit;
- SatNOGS cannot override BTK or other competent legal sources;
- absence from the curated snapshot does not mean a satellite/frequency does not exist;
- unknown aliases are never fuzzy-matched;
- current operational state is mutable and must be rechecked upstream when freshness matters.

## Examples

```bash
python scripts/satellite_lookup.py SO-50
python scripts/satellite_lookup.py AO-73
python scripts/ask.py "ISS APRS hangi frekansta?"
python scripts/ask.py "AO-91 uplink downlink nedir?"
```

## Data boundary

The snapshot intentionally excludes:

- TLE/orbital elements;
- observer/station identifiers;
- contributor/contact fields;
- telemetry frames;
- legal permission claims;
- automatically inferred operating status beyond the source-page snapshot.

## NEXT

Safe extensions can add more satellites or more fields only when they preserve:

1. source URL / upstream UUID provenance;
2. CC BY-SA 4.0 attribution and share-alike handling;
3. deterministic validation;
4. no legal-permission inference;
5. explicit freshness boundaries for mutable status.
