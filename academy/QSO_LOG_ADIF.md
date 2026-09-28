# Source-grounded QSO Log / ADIF Exporter

`scripts/qso_log_adif.py` exports a deliberately bounded Telsiz QSO record to ADIF 3.1.7 ADI.

Canonical technical source: `ADIF.SPEC.3.1.7`.

## Why the internal contract is separate

ADIF defines a data interchange format. It explicitly does not define an application's database schema. Telsiz therefore keeps a small application contract in `data/qso_log_contract.json` and maps only that supported subset to ADI.

For v1, a record requires:

- `CALL`
- `QSO_DATE`
- `TIME_ON`
- `MODE`
- at least one of `BAND` or `FREQ`

Optional supported fields are `RST_SENT`, `RST_RCVD`, `GRIDSQUARE`, and `COMMENT`.

## Fail-closed behavior

- unknown fields are rejected;
- dates and UTC times are validated;
- `FREQ` must be a positive finite decimal MHz value;
- the v1 ADI exporter accepts printable ASCII only;
- no field can be interpreted as a legal transmit verdict.

A successfully exported QSO proves only that the record satisfies this bounded interchange contract. It does **not** prove that the transmission was lawful.

## Usage

Input JSON:

```json
[
  {
    "CALL": "TA1ABC",
    "QSO_DATE": "20260929",
    "TIME_ON": "001530",
    "BAND": "2m",
    "MODE": "FM",
    "RST_SENT": "59",
    "RST_RCVD": "57"
  }
]
```

Export:

```bash
python scripts/qso_log_adif.py qso.json
python scripts/qso_log_adif.py qso.json --output qso.adi
```
