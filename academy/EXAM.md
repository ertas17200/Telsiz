# Grounded Practice Exam

The Telsiz exam engine is a **practice** tool. It is not labelled as an official KEGM question bank or as proof of current exam rules.

Canonical question bank: `academy/exam_questions.json`.

## Provenance contract

Every `source_grounded` question must link to verified source IDs and verified rule IDs. A rule's source must be explicitly present in the same question. Legal questions can use only current verified `official_legal` sources and verified legal rules.

Version 1 rejects:

- `official_exam_claim=true`;
- time-sensitive questions;
- pending sources;
- unverified candidate sources in grounded questions;
- hidden legal rules inside non-legal questions.

This keeps current fees, changing exam procedures and other freshness-sensitive details out of the bank until an explicit freshness contract and canonical source verification exist.

## Usage

List the practice bank:

```bash
python scripts/exam_simulator.py --list
```

Score selected answers:

```bash
python scripts/exam_simulator.py \
  --answer EXAM.TR.DUMMY-LOAD.001=A \
  --answer EXAM.TR.C144-POWER.001=B
```

The score is calculated against the full bank; unanswered questions remain unanswered. The output includes each question's source/rule IDs for traceability.
