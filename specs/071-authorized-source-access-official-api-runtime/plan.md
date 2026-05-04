# Implementation Plan: Authorized Source Access And Official API Runtime

## Scope

Implement row 071 as the authorized source slice. The runtime records official
API and credentialed read-session access without persisting secrets or
framework-native state in core.

## Technical Plan

- Add `AuthorizedSourceAccessRecord` contract rules for credential grant,
  credential audit, redacted artifacts, source anchors, content hashes, policy
  refs, command/event/outbox refs, and replay refs.
- Register authorized source commands/events and fixture oracles.
- Implement authorized-source report generation in the shared runtime.
- Expose `veracrawl-authorized-source`.

## Validation Plan

- Positive fixture: `tests/fixtures/production-authorized-source-success`.
- Contract, registry, runtime, fixture, and import-boundary tests under the
  production-grade test set.
