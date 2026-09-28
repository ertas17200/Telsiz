# RF Wavelength / Electrical-Length Calculator

`scripts/rf_wavelength.py` is a source-grounded, deterministic RF calculation tool.

## Source

`BIPM.SI.DEFINING_CONSTANTS` supplies the exact SI value:

`c = 299 792 458 m/s`

The calculation uses:

`lambda = c / f`

An optional user-supplied velocity factor scales the propagation wavelength:

`propagation_length = lambda * velocity_factor`

## Outputs

The tool returns:
- frequency in Hz;
- free-space wavelength in metres;
- propagation wavelength using the supplied velocity factor;
- one-quarter, one-half and one full propagation wavelength.

Supported input units are Hz, kHz, MHz and GHz.

## Important limitation

The quarter-wave and half-wave numbers are **ideal electrical lengths**. They are not guaranteed physical resonant antenna cut lengths.

Actual antenna dimensions can change because of conductor diameter, insulation, geometry, mounting, ground, nearby objects and end effects. Feed-line velocity factor also depends on the actual cable/material and should come from a trustworthy manufacturer specification or measurement.

The calculator does not decide whether a frequency, power level, emission or transmission is permitted. Every result has:

`"legal_verdict": null`

## Usage

```bash
python scripts/rf_wavelength.py 145.500 --unit MHz
python scripts/rf_wavelength.py 14.200 --unit MHz --velocity-factor 0.66
```
