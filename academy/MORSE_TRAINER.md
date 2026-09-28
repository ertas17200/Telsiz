# Source-grounded Morse Trainer

`scripts/morse_trainer.py` implements a deliberately limited International Morse training subset.

Canonical technical source: `ITU.R.M1677.1` — Recommendation ITU-R M.1677-1.

The repository stores only the A–Z and 0–9 mappings needed for the v1 training tool in `data/morse_code.json`; it does not reproduce the full Recommendation.

## Functions

- encode A–Z/0–9 text;
- decode the supported dot/dash signals;
- generate deterministic seeded practice prompts.

## Trust boundary

This is a technical/educational tool. It returns `legal_verdict: null` and does not decide licence rights, bands, power or permission to transmit.

## Usage

```bash
python scripts/morse_trainer.py encode "CQ TEST"
python scripts/morse_trainer.py decode "-.-. --.- / - . ... -"
python scripts/morse_trainer.py quiz --length 10 --seed 17200
```
