# Data Model: Production Run Control API

## ProductionProject

- `id`
- `owner_ref`
- `project_policy_refs`
- `default_budget_ref`
- `status`

## ProductionSiteScope

- `id`
- `project_ref`
- `allowed_scope_refs`
- `source_policy_refs`
- `robots_policy_ref`
- `egress_policy_ref`
- `credential_policy_ref`
- `status`

## RunBudget

- `id`
- `project_ref`
- `crawl_limit_refs`
- `max_pages`
- `max_depth`
- `max_runtime_seconds`
- `max_browser_minutes`
- `max_model_tokens`
- `policy_decision_refs`

## RunPolicySnapshot

- `id`
- `run_ref`
- `project_ref`
- `site_scope_ref`
- `source_policy_refs`
- `publication_policy_refs`
- `privacy_policy_ref`
- `egress_policy_ref`
- `credential_policy_ref`
- `prompt_taint_policy_ref`
- `budget_ref`
- `policy_decision_refs`

## RunApprovalRecord

- `id`
- `objective_ref`
- `plan_ref`
- `actor_ref`
- `approved`
- `approval_decision_ref`
- `rejection_reason_refs`
- `policy_decision_refs`

## RunLifecycleRecord

- `id`
- `run_ref`
- `action`
- `status_before`
- `status_after`
- `command_result_ref`
- `event_ref`
- `actor_ref`
- `policy_snapshot_ref`
- `budget_ref`
- `approval_record_ref`
- `failure_record_refs`
- `replay_refs`

## ProductionRunControlReport

- Aggregates project/site/objective/plan/run refs, approval, budget, policy,
  command, event, lifecycle, replay, status, operator status, and diagnostics.

## ProductionRunControlFixtureManifest

- Declares expected run-control status, completion result, operator status, and
  failure type for fixture execution.
