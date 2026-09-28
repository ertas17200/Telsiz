# Community Reference Review — arch-yunus/Amator-Telsiz-Rehberi

## Scope

Reference repository: `arch-yunus/Amator-Telsiz-Rehberi`

Reviewed on: 2026-09-28

Trust level: `community`

The repository is useful as a product/UX and tooling reference. It is **not** an authority for Turkish legal permission, frequency entitlement, licence-class rights or time-sensitive regulatory facts.

## Observed repository shape

The public repository exposes:

- `.github/`
- `LICENSE` (MIT)
- `README.md` and `README_EN.md`
- `ROADMAP.md`
- `assets/`
- `data/`
- `docs/`
- `requirements.txt`
- `scripts/`
- `tests/`

Examples of user-facing ideas present in the project include an exam simulator, Maidenhead/grid calculator, Morse trainer, Q-code trainer, RST helper, toroid calculator, QSO log template, repeater data, SDR/CHIRP documentation and bilingual documentation.

## Trust boundary

Nothing in this review changes the Telsiz source hierarchy.

Community content:

1. cannot establish a Turkish legal permission or prohibition;
2. cannot override BTK, KEGM, Resmî Gazete, Mevzuat or other higher-authority sources;
3. must not be copied into `data/rules.json` or `data/frequency_table.json` without independent grounding;
4. may contain time-sensitive or unsourced statements, so fees, licence thresholds, band powers and similar claims require separate verification;
5. may be used as inspiration for UX, educational flow, calculators and test scenarios.

If source code or text is directly reused or adapted, preserve the applicable MIT licence notice and attribution. Reimplementation from ideas should still record provenance in the engineering log when it materially shaped a feature.

## P11 adaptation backlog

### P11.1 — Academy layer

**Implementation status: IMPLEMENTED; every change remains subject to the repository CI gate before merge.**

The first Academy scaffold is machine-verifiable rather than a free-form content dump:

- `academy/academy.json` declares module provenance and trust status;
- `scripts/validate_academy.py` enforces source/rule/candidate boundaries;
- `tests/test_academy.py` locks the fail-closed contract;
- GitHub Actions runs the Academy validator before the unit test suite.

Acceptance:
- educational pages cite Telsiz source IDs or clearly say when content is general theory;
- legal facts never come from community content;
- `legal_verdicts=true` is rejected so Academy cannot bypass the decision engine;
- CI checks the manifest contract and regression tests.

### P11.2 — Grounded exam simulator

**Implementation status: IMPLEMENTED; every change remains subject to the repository CI gate before merge.**

The first practice engine uses `academy/exam_questions.json`, `scripts/validate_exam.py` and `scripts/exam_simulator.py`. It is deliberately marked `practice_only`, not an official KEGM simulator.

Acceptance:
- each grounded question carries explicit verified source/rule IDs;
- pending sources and unverified candidates are rejected from grounded questions;
- `official_exam_claim=true` and time-sensitive questions are rejected in v1;
- scoring logic has unit tests and preserves per-question provenance in output;
- no guessed KEGM fee or current exam-rule value is hard-coded.

### P11.3 — Operator tools

**Implementation status: IMPLEMENTED BASELINE. Grid Locator, Morse Trainer, Q-code/RS(T) Trainer, ADIF 3.1.7 QSO export, and a source-grounded RF wavelength/electrical-length calculator are implemented.**

Implemented:
- deterministic Maidenhead grid locator encoder;
- source-grounded ITU-R M.1677-1 Morse Trainer (A-Z/0-9 subset, encode/decode, seeded quiz);
- source-grounded Q-code/RS(T) Trainer with separate IARU/ITU provenance and deterministic practice prompts;
- bounded QSO record contract with source-grounded ADIF 3.1.7 ADI export;
- BIPM-grounded free-space wavelength and velocity-factor electrical-length calculator with explicit no-cut-length guarantee;
- 2/4/6-character Grid Locator precision;
- locator cell bounds/center decoder;
- strict global coordinate bounds and invalid-input rejection;
- round-trip/boundary/normalization unit tests;
- CLI output explicitly returns `legal_verdict: null`.

Baseline remaining: none. Antenna-specific design/cut-length calculators require separate source and assumption contracts before they may be added.

Acceptance:
- deterministic tools have unit tests and boundary cases;
- calculators state units and assumptions;
- tools do not emit legal-to-transmit verdicts outside the existing decision engine.

### P11.4 — Device manual knowledge

**Implementation status: IMPLEMENTED BASELINE for Yaesu FTM-400.**

The first manufacturer-manual layer uses Yaesu's official legacy product/download page and the separate DR/DE and XDR/XDE firmware information documents.

Implemented:
- exact DR/DE versus XDR/XDE model-family separation;
- explicit USA/AUS/EXP destination package selection;
- documented MAIN/DSP target metadata from the 22 Dec 2020 Yaesu update notices;
- operating-manual URLs recorded as `pending` because full files exceeded the current content-verification path;
- update steps withheld until the package-specific Yaesu Firmware Upgrade Manual is separately ingested and verified;
- no country-to-destination inference and no legal transmit verdict.

Acceptance:
- manufacturer manual/version metadata is recorded;
- firmware/update guidance is tied to exact model family and explicit destination;
- incompatible firmware families are programmatically rejected;
- manufacturer guidance remains separate from Turkish regulatory permission.

### P11.5 — Repeater and operating-practice data

A repeater/practice registry may be added only with source date and authority class.

Acceptance:
- community/association repeater lists are labelled operational guidance;
- official permission status is not inferred from a community list;
- stale records are detectable.

### P11.6 — Bilingual documentation

Add English navigation only after canonical Turkish source-backed content exists.

Acceptance:
- translations link to the same underlying source IDs;
- translation cannot silently alter legal meaning.

## Decision

Adopt the **product patterns**, not the unverified claims.

The current Telsiz architecture remains:

`official source -> structured source record -> grounded rule/data -> validator -> tests -> answer/tooling layer`.

P11 features must sit on top of that chain rather than bypass it.
