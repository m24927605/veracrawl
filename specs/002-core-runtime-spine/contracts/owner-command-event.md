# Contract: Owner Command Event

## Purpose

Define how runtime state changes move through command, owner service, result, and event boundaries.

## Command Handling Rules

Every mutating or publication-relevant action must include:

- `CommandEnvelope.id`
- `command_type`
- `target_aggregate_type`
- `target_aggregate_id`
- `owner_service`
- `payload_schema_ref`
- `idempotency_key`
- `causation_id`
- `correlation_id`
- `policy_decision_refs` when applicable
- `expected_version` for aggregate updates

## Owner Service Matrix

| Aggregate | Owner service | Required command families |
| --- | --- | --- |
| CrawlObjective | control | create/update/approve/archive objective |
| CrawlPlan | control | propose/approve/reject/supersede plan |
| CrawlRun | control | start/pause/resume/cancel/complete/fail run |
| SourceAdapterResult | natural adapter owner | execute/read/capture/import/apply/attach source |
| NormalizedDocument | normalize | normalize source/document |
| ExtractionCandidate | extract | create/reject/supersede candidate |
| EvidencePacket | evidence | build/validate evidence |
| VerificationDecision | verify | decide verification/conflict |
| PublishedOutput/OutputManifest | publish | publish/supersede/withdraw/expire output |
| ReplayBundleManifest | review_replay | build/validate replay |

## Event Requirements

Every accepted command must emit at least one event. Every rejected command must emit a rejection result with operator-visible reasons.

Required event families:

- command_received
- command_committed
- command_rejected
- policy_evaluated
- objective_created
- plan_proposed
- plan_approved
- processing_transitioned
- source_adapter_result_recorded
- snapshot_written
- evidence_built
- verification_decided
- output_published
- result_materialized
- replay_bundle_built
- error_recorded

## Rejection Rules

Commands must be rejected when:

- owner service does not match target aggregate
- expected version is stale
- policy decision is deny or missing where required
- required evidence, artifact, adapter result, or replay refs are missing
- a terminal state receives a non-terminal transition command
- a non-fetch adapter attempts to produce fetch/page snapshot semantics
