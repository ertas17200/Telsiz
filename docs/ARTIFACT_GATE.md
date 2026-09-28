# Official Artifact Gate

This gate closes the gap between **source content that can be rendered/read** and **byte-for-byte evidence that can be hashed**.

## Why it exists

A browser/PDF renderer can prove that a source was inspected, but it cannot by itself establish the exact artifact bytes used for a durable SHA-256 binding.

For legal/official source version control, Telsiz treats these as separate states:

```text
CONTENT_INSPECTED != BYTE_ARTIFACT_VERIFIED
```

## Registry

`data/artifacts.json` is the byte-evidence registry.

For the BTK Technical Criteria PDF it currently says:

```text
artifact_status=awaiting_bytes
sha256=null
change_status=UNKNOWN
reverify_required=true
```

This is intentional and fail-closed.

## Validate registry

```bash
python scripts/artifact_gate.py validate-registry
```

## Verify a downloaded official artifact

Once the exact official PDF bytes are available locally:

```bash
python scripts/artifact_gate.py verify-file \
  --source-id TR.BTK.FTM.TECH.2022-IK-SYD-245 \
  --file /path/to/ftm-teknik-olcutler-ek-5.pdf \
  --fetched-at 2026-09-28T20:00:00Z \
  --output /tmp/btk-artifact-observation.json
```

The command checks that:

- the file exists and is non-empty;
- a PDF source has a real `%PDF-` signature;
- MIME type matches the expected type;
- SHA-256 is calculated from streaming raw bytes;
- file size is recorded;
- the observed hash is compared with `data/sources.json -> content_sha256`.

## Change states

### HASH_OBSERVED_BIND_REQUIRED

The source registry has no prior hash.

This is the first byte-level observation. The new digest must be reviewed and explicitly bound to the source registry. It does **not** automatically make the semantic table complete.

### UNCHANGED

The observed digest exactly matches the canonical source hash.

```text
reverify_required=false
```

### SOURCE_CHANGED

The canonical URL now returns different bytes from the source registry's bound hash.

```text
reverify_required=true
```

The CLI returns a distinct non-zero status for `SOURCE_CHANGED`; derived legal data must be reverified before positive legal answers rely on it.

## No PDF storage requirement

The official PDF does not need to be committed to GitHub. The project can store only the provenance metadata, file size and cryptographic digest.

## P0 relationship

The current BTK raw transcription is 33/33 rows with 24/24 emission definitions, but P0 semantic promotion remains on HOLD until the artifact byte evidence is acquired and source conflicts are handled.

The artifact gate is infrastructure. Its own CI PASS must never be reported as the official BTK artifact itself being verified.
