# Feature Specification: Recommendation Ranking Publication Integration

**Feature Branch**: `088-optimization-owner-integration`
**Created**: 2026-05-06
**Status**: Implemented
**Input**: Spec 088 approved integration roadmap row 093.

## Purpose

Connect ranking score breakdowns and ranked output sets from specs 085, 087,
091, and 092 to publish/projection owner boundaries.

## Constitution Alignment

- Publication remains evidence-backed and verification-gated.
- Ranking changes order and explanation refs only; it never fabricates fields
  or changes verification decisions.
- Ranking profiles remain generic across offers, documents, records, tables,
  and factual outputs.

## Requirements

- **FR-093-001**: System MUST expose ranking/publication integration records
  with ranked output refs, ranking score refs, retained refs, suppressed refs,
  and publication gate refs.
- **FR-093-002**: System MUST rank retained evidence-backed outputs only.
- **FR-093-003**: System MUST preserve each retained output's verification
  status, evidence refs, and publication policy result.
- **FR-093-004**: System MUST record absent optional ranking features without
  fabricating price, availability, delivery, rating, review count, or seller
  reputation.

## Completion Gate

Ranking integration tests prove retained verified outputs are ranked with score
refs, duplicate penalties apply, source-limited penalties are visible, and
verification status is unchanged.

## Non-Goals

- This spec does not train learning-to-rank.
- This spec does not bypass publication gates.
