# Feature Specification: Canonical Dedupe Identity Integration

**Feature Branch**: `088-optimization-owner-integration`
**Created**: 2026-05-06
**Status**: Implemented
**Input**: Spec 088 approved integration roadmap row 092.

## Purpose

Connect canonicalization, fingerprints, identity decisions, duplicate
suppression, retained refs, and suppressed refs from specs 084, 087, 089, and
091 to scheduler, normalize, and graph owner boundaries.

## Constitution Alignment

- Dedupe remains generic across pages, articles, products, documents, records,
  and facts.
- Raw artifacts and source evidence are preserved even when duplicates are
  suppressed from publication.
- Embedding similarity remains advisory and cannot merge variants alone.

## Requirements

- **FR-092-001**: System MUST expose dedupe/identity integration records with
  canonical URL refs, fingerprint refs, identity decision refs, retained refs,
  and suppressed refs.
- **FR-092-002**: System MUST remove tracking/session/sort parameters while
  preserving semantic query, pagination, id, SKU, locale, and variant
  parameters.
- **FR-092-003**: System MUST suppress duplicates without deleting source
  artifacts or verified evidence.
- **FR-092-004**: System MUST preserve declared variants or route ambiguous
  identity cases to review.

## Completion Gate

Dedupe integration tests prove tracking duplicates are suppressed, variants are
preserved, identity decisions are replayable, and missing replay refs fail.

## Non-Goals

- This spec does not delete raw artifacts.
- This spec does not make embedding similarity authoritative.
