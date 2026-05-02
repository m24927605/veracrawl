# Data Model: Operational Disaster Recovery Gate

## DRRestorePlan

Declares the approved restore scope, restore point, backup manifest, ordered phases, validation gates, rollback behavior, and approval refs.

Required fields:

- `id`
- `restore_scope_ref`
- `restore_point_ref`
- `backup_manifest_ref`
- `metadata_snapshot_ref`
- `artifact_snapshot_refs`
- `event_cursor_refs`
- `ordered_phase_refs`
- `phase_order`
- `required_validation_gate_refs`
- `policy_decision_refs`
- `approval_decision_refs`

Validation rules:

- ordered phases must include metadata restore, artifact reachability, event replay, projection rebuild, export reconciliation, reference validation, and report publication
- phase order must be strictly increasing
- policy refs are always required
- approval refs are required for executable restore plans

## DRRestoreRun

Records execution of a restore plan through ordered phases.

Required fields:

- `id`
- `dr_restore_plan_id`
- `restore_scope_ref`
- `phase_results`
- `current_phase`
- `status`
- `emitted_event_refs`
- `policy_decision_refs`

Validation rules:

- completed runs require every required phase to be completed and event refs present
- failed runs require failure record refs
- needs-review runs require unresolved refs or validation warnings

## DRRestoreReport

Existing ops report extended for operational DR gate refs.

Pass requires:

- restore scope ref
- restore plan/run refs
- restore point and backup manifest refs
- metadata restore ref
- artifact reachability report ref
- event replay report ref
- projection rebuild job refs
- export reconciliation refs
- queue recovery refs
- runtime infrastructure report refs
- policy refs
- command refs
- event cursor refs
- outbox refs
- replay bundle ref
- validation refs
- no unresolved refs
- no data loss

Non-pass requires:

- failure refs, missing refs, unresolved refs, contract-only refs, or data loss diagnostics

## DRRestoreFixtureManifest

Declares fixture scenario, expected completion result, expected operator status, and optional expected failure type.

Scenarios:

- `dr-restore-success`
- `dr-restore-runtime-unavailable`
- `dr-restore-missing-metadata`
- `dr-restore-missing-artifact-reachability`
- `dr-restore-missing-event-replay`
- `dr-restore-missing-projection-rebuild`
- `dr-restore-missing-export-reconciliation`
- `dr-restore-unresolved-refs`
- `dr-restore-data-loss`
- `dr-restore-unsafe-recovery-without-approval`

## FailureRecord

Uses `disaster_recovery` or `unsafe_recovery_without_review` failure types for deterministic DR negative cases.

## RecoveryAction

Uses `restore_from_backup`, `replay_events`, `rebuild_projection`, `reconcile_export`, or `request_review` action types depending on failure class. Side-effecting recovery requires policy and approval refs.
