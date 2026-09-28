# Türkiye Repeater Operational Snapshot

This P11.5 layer deliberately separates **operational information** from **official permission**.

## Sources

Operational source:

- `TR.TRAC.REPEATER.LIST` — TRAC "Röle Bilgileri" page.

Legal/authority context:

- `TR.BTK.RADIO.PROCEDURES` — BTK's current official rules for repeater/link systems established by amateur-radio associations.

BTK states that association repeater systems are handled through frequency allocation and permission/licensing procedures. Therefore a TRAC row marked `Aktif` is useful operational information but is **not** treated as proof of BTK permission.

## Initial snapshot

`data/repeaters.json` is intentionally:

`coverage_status = partial_snapshot`

The first snapshot contains 15 directly observed entries across VHF/UHF and includes both `Aktif` and `Bakımda` examples.

Absence from the repository snapshot never means a repeater does not exist.

Every association-derived row carries:

`official_permission_status = UNKNOWN_NOT_VERIFIED`

## Freshness

The snapshot stores its observation timestamp. The repository uses a 30-day stale threshold as an engineering freshness policy.

That threshold is **not** a statement from TRAC or BTK.

Use:

```bash
python scripts/repeater_lookup.py freshness --as-of 2026-10-29T22:12:01Z
```

## Search

```bash
python scripts/repeater_lookup.py search --branch KADIKÖY
python scripts/repeater_lookup.py search --site KARTEPE --band UHF
python scripts/repeater_lookup.py search --status Bakımda
```

Search results preserve the source's operational status and always return:

`"legal_verdict": null`

For a legal/permission question, the separate official BTK chain must be used.
