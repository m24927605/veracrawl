# Feature Specification: Drift Recovery Feedback Runtime

**Feature Branch**: `088-optimization-owner-integration`
**Created**: 2026-05-06
**Status**: Implemented
**Input**: Spec 088 approved integration roadmap row 095.

## Purpose

Connect selector drift, retry classification, repair outcomes, failure memory
refs, and future optimization feedback from specs 083, 086, 091, and 094 to
review/replay and ops boundaries.

## Constitution Alignment

- Drift and repair feedback informs future planning but cannot become source
  evidence.
- Repairs must flow through owner-service commands and verification gates.
- Unsafe recovery, owner bypass, or policy weakening fails integration.

## Requirements

- **FR-095-001**: System MUST expose drift/recovery feedback records with
  drift type, affected refs, retry class, repair outcome, memory advisory refs,
  policy refs, and replay refs.
- **FR-095-002**: System MUST classify selector drift, template drift, field
  validation drift, stale cache, timeout retry, and source-limited failures.
- **FR-095-003**: System MUST fail unsafe recovery, owner-service bypass,
  policy weakening, and memory-as-evidence attempts.
- **FR-095-004**: System MUST make feedback available to future optimization
  decisions only as advisory signals.

## Completion Gate

Drift/recovery tests prove repair feedback is typed, replayable, advisory, and
blocked when unsafe or evidence-bypassing.

## Non-Goals

- This spec does not implement autonomous selector patch deployment.
- This spec does not enable memory-derived publication evidence.
