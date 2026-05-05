# Feature Specification: Extraction Fallback Verification Integration

**Feature Branch**: `088-optimization-owner-integration`
**Created**: 2026-05-06
**Status**: Implemented
**Input**: Spec 088 approved integration roadmap row 091.

## Purpose

Connect extractor fallback plans, attempts, field confidence, abstention, and
review routing from specs 083, 087, and 090 to extract/verify owner boundaries.

## Constitution Alignment

- Extract/verify remain responsible for source-backed acceptance and rejection.
- LLM output can assist extraction only as bounded structured fallback and can
  never be source evidence.
- Low-confidence and unanchored values abstain or route to review.

## Requirements

- **FR-091-001**: System MUST expose extract/verify integration records with
  extractor plan refs, attempt refs, confidence refs, abstention refs, and
  review refs.
- **FR-091-002**: System MUST accept deterministic source-backed attempts before
  LLM fallback attempts.
- **FR-091-003**: System MUST reject LLM-only, graph-only, memory-only, and
  ranking-only values as evidence.
- **FR-091-004**: System MUST validate price, currency, availability, title,
  URL, and image-like fields before publication eligibility.

## Completion Gate

Extract/verify integration tests prove source-backed fields are accepted,
LLM-only fields are rejected, low-confidence fields abstain, and validation refs
are replayable.

## Non-Goals

- This spec does not publish extraction candidates directly.
- This spec does not train extraction models.
