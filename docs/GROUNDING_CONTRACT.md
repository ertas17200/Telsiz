# Claim-Level Grounding Contract

The source registry answers **where information came from**. The rule registry answers **which claim may be made from that source**.

## Why this exists

An AI can cite a real source and still make a claim the source does not support. Telsiz therefore stores important answerable claims as structured rules in `data/rules.json`.

## Fail-closed requirements

A rule marked `verified` must:

- reference an existing source;
- reference a source that is itself `verified`;
- carry a usable source locator;
- carry a verification timestamp;
- use an authority level compatible with the source type;
- when `authority=legal`, cite a `current` `official_legal` source.

A pending legal source can be indexed for discovery, but it cannot support a verified legal rule.

## Answer construction order

1. Match the question to candidate rule tags/parameters.
2. For legal questions, use verified legal rules first.
3. Apply all conditions and limits associated with the selected rule.
4. Add amateur-practice guidance only after legal constraints are resolved.
5. Cite the underlying source record and locator.
6. If no verified rule covers the requested claim, say that exact verification is still required.

## Frequency/power questions

A frequency being present in an IARU or association band plan is not enough to answer "Can I legally transmit here in Türkiye?"

The answer engine must first resolve:

- jurisdiction;
- licence class;
- frequency range;
- transmitter/output-power restriction;
- emission/mode restriction;
- device-specific restrictions;
- special sub-band restrictions (repeater, beacon, satellite, emergency use, etc.).

Only then may it add IARU/TRAC operating guidance.

## Initial rule set

The first rule set intentionally covers a small number of high-confidence provisions from BTK Technical Criteria Article 22 and sample power limits for C-class operation. It is not yet a complete transcription of the amateur frequency table.

Completeness must never be inferred from the presence of some rules.
