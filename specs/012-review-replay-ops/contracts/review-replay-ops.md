# Review Replay Ops Contracts

This feature materializes the target review/replay/ops console data surface.

Required contracts:

- `ReviewItem`
- `ReplayAuditView`
- `FailureRecord`
- `RecoveryAction`
- `DRRestoreReport`
- `QualityReport`
- `OpsDashboardSnapshot`
- `OpsConsoleReport`
- `OpsFixtureManifest`

Required commands:

- `record_review_item`
- `record_replay_audit_view`
- `record_failure_record`
- `record_recovery_action`
- `record_dr_restore_report`
- `record_quality_report`
- `record_ops_dashboard_snapshot`
- `record_ops_console_report`

Required events:

- `review_item_recorded`
- `replay_audit_view_recorded`
- `failure_recorded`
- `recovery_action_recorded`
- `dr_restore_reported`
- `quality_report_recorded`
- `ops_dashboard_snapshot_recorded`
- `ops_console_reported`

Required fixtures:

- `review-console-success`
- `replay-audit-success`
- `quality-dashboard-success`
- `missing-review-evidence`
- `unresolved-failure-without-recovery`
- `stale-dashboard-projection`
- `unsafe-recovery-without-review`

Non-completion boundary: these contracts do not claim production UI, production observability storage, production alerting, distributed queue/store adapters, export delivery, or production scale readiness.
