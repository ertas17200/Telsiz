# Official Artifact Byte Acquisition

The repository's normal validation remains network-independent. Live official artifact acquisition is separated into an explicit observation command.

## Observe a registered canonical source

```bash
python scripts/fetch_official_artifact.py \
  --source-id TR.BTK.FTM.TECH.2022-IK-SYD-245 \
  --fetched-at 2026-09-29T10:30:00Z
```

The command:

- accepts only a registered `source_id`; callers cannot supply an arbitrary URL;
- requires the registered canonical URL to use HTTPS;
- rejects cross-origin redirects;
- requires the HTTP content type to match the artifact registry;
- enforces a maximum download size;
- reuses the byte-oriented PDF signature, size and SHA-256 checks in `artifact_gate.py`;
- emits an observation with `HASH_OBSERVED_BIND_REQUIRED`, `UNCHANGED`, or `SOURCE_CHANGED`;
- never edits `data/sources.json` or `data/artifacts.json`.

A first observed hash is review evidence, not an automatic source binding.

## GitHub Actions

`.github/workflows/p0-artifact-observation.yml` is the dedicated live observation workflow. The temporary P0 probe branch trigger is used only while establishing the first byte observation. Before merge, the workflow must be reduced to manual `workflow_dispatch` so normal CI does not depend on external source availability.
