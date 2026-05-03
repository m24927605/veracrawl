# Data Model: Ops Console, Replay, And Observability Runtime

## OpsReplayObservabilityRuntimeReport

Top-level row 053 aggregate proving an operator can inspect and recover a run
through canonical refs.

Required for pass:

- dependency refs: `result_publication_export_report_ref`,
  `worker_orchestration_runtime_report_ref`, `ops_console_report_ref`,
  `observability_report_ref`
- operator refs: run-control action, review item, evidence review, replay audit,
  graph/debug, export status, withdrawal status, recovery, failure, DR restore,
  quality, dashboard, alert, runbook, cost, signal, metric, trace
- lineage refs: policy, command, event cursor, outbox, redaction map,
  replay bundle

Pass is rejected when typed failures, missing refs, stale dashboard refs,
unresolved recovery refs, unsafe operator action refs, observability gaps, or
replay gaps are present.

Non-pass requires:

- `failure_type`
- at least one of `failure_report_refs`, `missing_ref_fields`,
  `stale_dashboard_refs`, `unresolved_recovery_refs`,
  `unsafe_operator_action_refs`, `observability_gap_refs`, or `replay_gap_refs`

## OpsReplayObservabilityFixtureManifest

Fixture manifest for target-profile deterministic row 053 fixtures.

Required:

- `target` profile
- expected completion result and operator status
- expected failure type for negative cases
- required ref types list

## Failure Types

- `ops_runtime_missing_publication`
- `ops_runtime_missing_worker_orchestration`
- `ops_runtime_missing_ops_console`
- `ops_runtime_missing_observability`
- `ops_runtime_stale_dashboard`
- `ops_runtime_unresolved_recovery`
- `ops_runtime_unsafe_operator_action`
- `ops_runtime_replay_mismatch`
