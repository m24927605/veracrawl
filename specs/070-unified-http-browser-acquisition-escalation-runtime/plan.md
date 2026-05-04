# Implementation Plan: Unified HTTP Browser Acquisition Escalation Runtime

## Scope

Implement row 070 as the acquisition escalation slice. The runtime records HTTP
and browser acquisition attempts, source anchors, artifacts, content hashes,
source limitation refs, policy refs, command/event/outbox refs, and replay refs.

## Technical Plan

- Add `AcquisitionAttemptRecord` production-grade contract rules.
- Register acquisition commands/events and fixture oracles.
- Implement pass and source-limited acquisition branches in the shared
  production-grade runtime.
- Expose `veracrawl-acquisition-escalation`.
- Preserve the rule that source-limited pages are recorded as needs-review
  instead of fabricated evidence.

## Validation Plan

- Positive fixture: `tests/fixtures/production-acquisition-escalation-success`.
- Source-limited fixture:
  `tests/fixtures/production-acquisition-source-limited`.
- Contract, runtime, fixture, registry, and import-boundary tests under the
  production-grade test set.
