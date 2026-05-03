# Feature Specification: Live Normalization And Site Understanding

**Feature Branch**: `045-live-normalization-site-understanding`
**Created**: 2026-05-03
**Status**: Active
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Convert acquired live artifacts into normalized documents, source anchors, link
provenance or no-link analysis, page type classifications, site models, and
replayable normalization manifests without treating derived site understanding
as source evidence.

## User Stories

### US1 - Normalize Live Acquired Artifacts (P1)

As a crawl operator, I need live HTTP, structured source, and browser snapshot
prerequisite refs to produce normalized documents, anchor maps, page type
classification, link provenance when outbound links exist, no-link analysis
when they do not, site model refs, policy refs, command/event refs, and replay
refs.

**Independent Test**: Run `live-normalization-listing-success` through the CLI
and assert a passing report with all normalization/site-understanding refs.

### US2 - Fail Incomplete Or Unsafe Normalization (P1)

As a reviewer, I need missing upstream refs, empty normalized content, missing
anchors, missing site model, and replay mismatch to fail deterministically.

**Independent Test**: Run all negative live-normalization fixtures and assert
typed failure diagnostics.

## Functional Requirements

- **FR-001**: Core live normalization runtime MUST receive acquired content and
  upstream report refs through explicit inputs; it MUST NOT import concrete
  network, browser, source, model, or agent framework adapters.
- **FR-002**: Passing reports MUST include live HTTP, structured source, and
  browser snapshot refs; normalized document refs; normalization manifest refs;
  anchor map/source anchor refs; link analysis refs; page type refs; site model
  refs; artifact refs; policy refs; command/event/outbox refs; and replay refs.
  Pages with outbound links MUST include link provenance refs; pages without
  outbound links MUST include a deterministic no-link analysis ref instead of
  fabricated link provenance.
- **FR-003**: Page/site understanding refs MUST be treated as derived planning
  context, not source evidence or published output.
- **FR-004**: Missing upstream refs, empty content, missing anchors, missing
  site model, and replay mismatch MUST fail with typed diagnostics.

## Dependencies

- Blocks: 046, 047, 049, 051, 052, 054.
- Requires: 041, 042, 043.

## Completion Gate

Real acquired artifacts produce replayable normalization manifests, source
anchors, site models, and honest link provenance/no-link analysis across target
website patterns.

## Non-Goals

- Does not publish outputs.
- Does not treat site model or graph context as source evidence.
