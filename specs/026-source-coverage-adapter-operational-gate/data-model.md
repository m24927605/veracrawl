# Data Model: Source Coverage Adapter Operational Gate

## SourceCoverageAdapterExecutionRecord

- `id`
- `adapter_type`
- `natural_result_type`
- `source_adapter_spec_ref`
- `source_adapter_result_ref`
- `natural_result_refs`
- `fetch_attempt_refs`
- `page_snapshot_refs`
- `browser_interaction_refs`
- `credential_audit_refs`
- `document_artifact_refs`
- `api_payload_refs`
- `command_result_refs`
- `policy_decision_refs`
- `observability_report_refs`
- `security_privacy_report_refs`
- `replay_bundle_ref`
- `live_runtime_refs`
- `contract_adapter_refs`
- `diagnostic_adapter_state_refs`
- `raw_secret_persisted`
- `adapter_native_state_canonical`
- `unsafe_browser_side_effect_refs`
- `missing_ref_fields`
- `result`

## SourceCoverageAdapterReport

- `id`
- `run_ref`
- `adapter_execution_refs`
- `required_adapter_types`
- `verified_adapter_types`
- `source_adapter_result_refs`
- `natural_result_refs`
- `fetch_attempt_refs`
- `page_snapshot_refs`
- `browser_interaction_refs`
- `credential_audit_refs`
- `document_artifact_refs`
- `api_payload_refs`
- `policy_decision_refs`
- `observability_report_refs`
- `security_privacy_report_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `contract_only_refs`
- `missing_runtime_refs`
- `raw_secret_leak_refs`
- `adapter_native_state_canonical_refs`
- `unsafe_browser_side_effect_refs`
- `unsupported_adapter_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`

## SourceCoverageAdapterFixtureManifest

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`
