# Source-grounded Q-code and RS(T) Trainer

`scripts/qcode_rst_trainer.py` provides a deliberately bounded operator-training tool.

## Provenance

Q-code training:
- `IARU.R1.EOP.4.2.0` — Chapter 10 / Table 10-A, current amateur operating-practice subset;
- `ITU.R.M1172.0` — Annex 1, Section I, standardized Q-code technical provenance.

RS(T) training:
- `IARU.R1.EOP.4.2.0` — Section 13.4;
- `IARU.R1.VHF.HANDBOOK.10.02` — Section 19.1 Signal Reporting System.

The stored descriptions are concise paraphrases for training; the repository does not reproduce the source documents.

## Supported v1 functions

- lookup of the 20 Q-codes included in the current IARU EOP Table 10-A;
- deterministic seeded Q-code flashcards;
- numeric two-digit RS interpretation for phone;
- numeric three-digit RST interpretation for CW;
- deterministic seeded RS(T) practice reports.

V1 intentionally does not parse `59+15`, suffix letters, contest-specific exchanges, or other extended reporting conventions.

## Trust boundary

This is operating-practice training, not a legal permission engine.

Every CLI result returns:

`"legal_verdict": null`

The tool does not decide licence rights, bands, power, emissions, or permission to transmit. Turkish legal questions remain delegated to the repository's fail-closed decision engine.

## Usage

```bash
python scripts/qcode_rst_trainer.py qcode QRZ
python scripts/qcode_rst_trainer.py qquiz --seed 17200
python scripts/qcode_rst_trainer.py rst 59 --mode phone
python scripts/qcode_rst_trainer.py rst 599 --mode cw
python scripts/qcode_rst_trainer.py rstquiz --mode cw --seed 17200
```
