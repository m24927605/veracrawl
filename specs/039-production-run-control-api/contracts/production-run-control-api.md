# Contract: Production Run Control API

## Contracts

- `ProductionProject`
- `ProductionSiteScope`
- `RunBudget`
- `RunPolicySnapshot`
- `RunApprovalRecord`
- `RunLifecycleRecord`
- `ProductionRunControlReport`
- `ProductionRunControlFixtureManifest`

## Commands

- `record_production_project`
- `record_production_site_scope`
- `record_run_budget`
- `record_run_policy_snapshot`
- `record_run_approval`
- `start_run`
- `pause_run`
- `resume_run`
- `cancel_run`
- `fail_run`
- `complete_run`
- `record_production_run_control_report`

## Events

- `production_project_recorded`
- `production_site_scope_recorded`
- `run_budget_recorded`
- `run_policy_snapshot_recorded`
- `run_approval_recorded`
- `run_started`
- `run_paused`
- `run_resumed`
- `run_cancelled`
- `run_failed`
- `run_completed`
- `production_run_control_reported`

## Fixtures

- `production-run-control-success`
- `production-run-control-paused-resumed`
- `production-run-control-cancelled`
- `production-run-control-policy-denied`
- `production-run-control-missing-approval`
- `production-run-control-missing-budget`
- `production-run-control-invalid-transition`
- `production-run-control-missing-replay`
