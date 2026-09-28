# Telsiz AI Knowledge Base — Project Scope

## Mission

This repository provides a source-grounded knowledge base for AI systems answering questions about amateur radio, with an initial focus on Türkiye.

The system must distinguish between:

1. **Legal / regulatory information** — statutes, regulations, official decisions, official notices, licensing rules, allocations and other material issued by competent public authorities.
2. **Amateur-radio / technical information** — trusted amateur-radio associations, technical manuals, training material, standards-oriented references and established amateur-radio publications.

## Core principle

**LEGAL / OFFICIAL > OFFICIAL TECHNICAL > TRUSTED AMATEUR PUBLICATION > COMMUNITY**

A lower-trust source must never silently override a higher-trust source.

## Required answer behaviour

An AI using this repository must:

- cite the source for legal or regulatory claims;
- distinguish law from common amateur practice;
- state uncertainty instead of inventing facts;
- preserve the publication/effective/status metadata of legal material;
- prefer primary official sources over commentary;
- not present an expired, superseded or unverified rule as current;
- clearly label community-derived guidance;
- warn when a question requires current source verification.

## Initial jurisdiction

Türkiye (TR). The data model is designed to support additional jurisdictions later.

## Initial subject areas

- amateur-radio licensing and authorization;
- call signs and station identification;
- frequency allocations and band plans;
- permitted/prohibited operation;
- operating procedures;
- antennas and RF basics;
- propagation;
- digital modes;
- emergency communications;
- equipment and station setup;
- interference and good operating practice.

## Non-goal

This repository is not itself a legal authority. It is a structured, auditable index and knowledge layer over traceable sources.
