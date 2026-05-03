# Feature Specification: Result Publication And Export Runtime

**Feature Branch**: `048-result-publication-export-runtime`
**Status**: Planned - implementing
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Materialize published results, Result API responses, output manifests, export
receipts, local production exports, and withdrawal/correction refs.

## Scope

- Published output and output manifest runtime.
- Result API and local JSON/structured materialization.
- Export delivery receipt and export reconciliation records.
- Withdrawal, correction, and redaction propagation refs.

## Dependencies

- Blocks: 053, 054.
- Requires: 047.

## Completion Gate

Published outputs and exports are evidence-backed, replayable, withdrawable, and
blocked when publication, privacy, policy, or export gates fail.

## Functional Requirements

- **FR-001**: Passing runtime reports MUST include row 047 live evidence refs,
  extraction candidate refs, evidence coverage/packet/manifest refs,
  verification/review refs, publication report refs, published output refs,
  output manifest refs, Result API snapshot refs, export target/job/attempt
  refs, delivery receipt refs, withdrawal/correction refs, destination mapping
  refs, policy/privacy refs, command/event/outbox refs, and replay refs.
- **FR-002**: Published outputs MUST be produced only by source-backed evidence
  and accepted verification/review decisions. Candidate-only or graph/memory
  derived context MUST NOT be publishable.
- **FR-003**: Result API snapshots MUST reference immutable published outputs
  and output manifests, carry a response artifact/hash, and preserve privacy
  lifecycle and replay refs.
- **FR-004**: Local export materialization MUST create destination-neutral
  export target specs, jobs, attempts, delivery receipts, destination object
  mappings, withdrawal refs, correction refs, policy refs, and replay refs.
- **FR-005**: Publication policy denial, verification not accepted, missing
  output manifests, missing delivery receipts, missing withdrawal propagation,
  corrections without withdrawal, missing privacy refs, direct export bypass,
  and replay mismatch MUST produce typed non-pass reports.
- **FR-006**: VeraCrawl core MUST remain low-coupled and framework-neutral:
  no concrete source/browser/model/agent/storage/export connector imports may be
  used by the 048 core aggregate runtime.

## Required Fixtures

- `result-publication-export-success`
- `result-publication-api-success`
- `result-publication-correction-withdrawal-success`
- `result-publication-missing-live-evidence`
- `result-publication-policy-denied`
- `result-publication-verification-not-accepted`
- `result-publication-missing-output-manifest`
- `result-publication-export-missing-receipt`
- `result-publication-withdrawal-missing-propagation`
- `result-publication-correction-without-withdrawal`
- `result-publication-privacy-missing`
- `result-publication-direct-export-bypass`
- `result-publication-replay-mismatch`

## Non-Goals

- Does not implement every external warehouse/SaaS connector.
- Does not allow export-native state to become canonical state.
