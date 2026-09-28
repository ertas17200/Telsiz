# Maidenhead Grid Locator Tool

`scripts/grid_locator.py` is a deterministic educational operator tool.

It converts latitude/longitude to 2-, 4-, or 6-character Maidenhead locators and can return the geographic bounds/center of a locator cell.

## Trust boundary

This tool is attached to the Academy module `ACADEMY.TOOL.GRID-LOCATOR`, which is `educational_only`.

It does **not**:

- decide whether transmission is legal;
- grant a frequency/band entitlement;
- infer licence class permissions;
- turn a community reference into an official source.

Its CLI output explicitly leaves `legal_verdict` as `null`.

## Coordinate contract

Encoding uses half-open global bounds:

- `-90 <= latitude < 90`
- `-180 <= longitude < 180`

Supported precision is 2, 4, or 6 characters.

## Usage

```bash
python scripts/grid_locator.py encode --lat 41.0082 --lon 28.9784 --precision 6
python scripts/grid_locator.py bounds KN41la
```

The implementation uses only the Python standard library and is covered by unit tests for boundary, normalization, round-trip and invalid-input behavior.
