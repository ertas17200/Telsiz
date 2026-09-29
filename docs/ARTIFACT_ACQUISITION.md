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

The first BTK baseline observation completed on GitHub Actions run `36559259435`, job `109375881365`: `508766` bytes, SHA-256 `eff832fc30df1adf60e4a8c514a6069154d526d3ab88ae803b51a5536d103db0`. The observation was explicitly reviewed before binding.

## GitHub Actions

`.github/workflows/p0-artifact-observation.yml` is the dedicated live observation workflow and is manual-only via `workflow_dispatch`. Normal validation stays network-independent; live source availability cannot make ordinary repository CI flaky.
