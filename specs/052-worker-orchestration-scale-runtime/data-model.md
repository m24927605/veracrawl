# Data Model: Worker Orchestration And Scale Runtime

## WorkerOrchestrationRuntimeReport

Fields:

- `id`, `fixture_id`, `run_ref`
- dependency refs:
  - `production_persistence_runtime_report_ref`
  - `queue_broker_conformance_report_ref`
  - `live_http_acquisition_report_ref`
  - `live_normalization_runtime_report_ref`
  - `live_evidence_verification_runtime_report_ref`
  - `scale_recovery_report_ref`
- worker refs:
  - `worker_pool_refs`
  - `worker_heartbeat_refs`
  - `worker_capacity_refs`
- queue and lease refs:
  - `queue_topology_ref`
  - `queue_item_refs`
  - `shard_lease_refs`
  - `lease_heartbeat_refs`
  - `fencing_token_refs`
  - `visibility_timeout_refs`
  - `fairness_scope_refs`
- reliability refs:
  - `retry_refs`
  - `dead_letter_refs`
  - `failure_record_refs`
  - `recovery_action_refs`
  - `duplicate_suppression_refs`
  - `backpressure_signal_refs`
  - `autoscaling_decision_refs`
  - `pending_outbox_refs`
  - `event_gap_refs`
- replay and policy refs:
  - `policy_decision_refs`
  - `command_record_refs`
  - `event_cursor_refs`
  - `outbox_refs`
  - `replay_bundle_ref`
- failure diagnostics:
  - `failure_type`
  - `failure_report_refs`
  - `missing_ref_fields`
  - `hidden_dead_letter_refs`
  - `duplicate_pollution_refs`
  - `unrecovered_stale_lease_refs`
  - `diagnostics`
- result:
  - `operator_status`
  - `completion_result`

Validation:

- `pass` requires every dependency, worker, queue, lease, reliability, policy,
  command/event/outbox, and replay group.
- `pass` rejects failure type, missing refs, hidden dead letters, duplicate
  pollution, and unrecovered stale leases.
- non-pass requires a typed failure plus failure refs, missing refs, or explicit
  violation refs.

## WorkerOrchestrationFixtureManifest

Fields:

- `id`, `scenario`, `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`
- `required_ref_types`

Validation:

- target profile is required.
- required ref types are explicit.
- negative fixtures must not expect pass and must include expected failure type.

## State Transitions

```text
planned -> dependencies_checked -> workers_registered -> leased -> heartbeated -> completed -> pass
planned -> leased -> worker_crashed -> retry_or_dead_letter -> recovered -> pass
planned -> leased -> stale_lease -> unrecovered -> fail(stale_lease_unrecovered)
planned -> backpressure_detected -> autoscale_without_policy -> fail(backpressure_without_policy)
planned -> replay_checked -> replay_mismatch -> fail(replay_mismatch)
```
