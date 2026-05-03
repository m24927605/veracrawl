# Data Model: VeraCrawl Target Product Acceptance Gate

## Enums

- `TargetProductWorkflow`: `multi_site_onboarding`, `objective_to_plan_approval`, `dynamic_auth_document_api_crawl`, `evidence_review`, `conflict_resolution`, `drift_repair`, `memory_reuse`, `export_and_withdrawal`, `replay_and_audit`, `operator_recovery`.
- `MinimumProductGate`: `approved_plan_creation`, `reviewer_time_per_output`, `drift_repair_success`, `operator_recovery_completion`, `export_withdrawal_reconciliation`, `user_facing_status_accuracy`, `buyer_value_workflow_pass`.
- `ProductAcceptanceFailureType`: typed negative outcomes for missing workflows, missing gates, missing refs, scaffold/contract-only claims, false completion labels, degraded-operational labels, and export reconciliation gaps.

## ProductWorkflowReadinessRecord

Required fields:

- `id`, `run_ref`, `fixture_id`, `workflow`
- `buyer_value_ref`
- `evidence_refs`
- `replay_refs`
- `operator_visible_result_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `artifact_refs`
- `acceptance_oracle_refs`
- `minimum_gate_refs`
- `workflow_specific_refs`
- `capability_state_refs`
- `status_accuracy_refs`
- `failure_oracle_refs`
- `missing_ref_fields`
- diagnostic refs for scaffold-only, contract-only, false-complete, degraded-operational, and export reconciliation failures

Validation:

- Passing records require all baseline refs and workflow-specific refs.
- Passing records reject scaffold-only refs, contract-only refs, false-complete refs, degraded-operational refs, export reconciliation gap refs, and missing fields.
- `export_and_withdrawal` requires export reconciliation refs.
- `operator_recovery` requires recovery action refs.
- `dynamic_auth_document_api_crawl` requires browser/auth/document/API safety refs.

## ProductAcceptanceGateReport

Required fields:

- `id`, `run_ref`, `fixture_id`
- `workflow_record_refs`
- `covered_workflows`
- `minimum_gate_refs`
- `buyer_value_workflow_refs`
- `evidence_refs`
- `replay_refs`
- `operator_visible_result_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `artifact_refs`
- `status_accuracy_refs`
- `completion_result`
- `operator_status`
- `failure_type`
- failure diagnostic refs
- `contract_only_refs`
- `missing_runtime_refs`

Validation:

- `pass` requires exactly all target workflows, all minimum gates, no failure type, no missing refs, and all baseline refs.
- `needs_review` requires contract-only or missing-runtime refs and cannot be used as pass.
- `fail` requires a typed `failure_type`.

## ProductAcceptanceFixtureManifest

Required fields:

- `fixture_id`
- `profile`
- `scenario`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`
- `contract_only`
- `created_at`

Validation:

- Target profile is required.
- Negative fixtures cannot expect pass.
- Expected failure type requires `negative_case`.
