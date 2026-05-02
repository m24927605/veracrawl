# Data Model: Model Provider Adapter Operational Gate

## ModelProviderAdapterExecutionRecord

Per-provider execution record.

- `id`
- `provider_name`
- `runtime_spec_ref`
- `model_request_ref`
- `model_response_ref`
- `model_call_trace_ref`
- `context_bundle_trace_ref`
- `agent_run_request_ref`
- `agent_run_result_ref`
- `agent_action_trace_ref`
- `command_result_refs`
- `policy_decision_refs`
- `observability_report_refs`
- `security_privacy_report_refs`
- `replay_bundle_ref`
- `live_runtime_refs`
- `contract_adapter_refs`
- `diagnostic_provider_state_refs`
- `raw_prompt_persisted`
- `raw_response_persisted`
- `raw_credential_persisted`
- `provider_transcript_canonical`
- `unsafe_tool_suggestion_refs`
- `missing_ref_fields`
- `result`

Pass validation requires all canonical refs, policy, observability, security/privacy, replay, and either live runtime or contract adapter refs. `needs_review` requires contract-only or missing-runtime refs. Raw prompt/response/credential persistence and provider-native canonical state are invalid.

## ModelProviderAdapterReport

Gate-level result aggregating provider execution records.

- `id`
- `run_ref`
- `provider_execution_refs`
- `required_provider_names`
- `verified_provider_names`
- `model_request_refs`
- `model_response_refs`
- `model_call_trace_refs`
- `context_bundle_trace_refs`
- `agent_run_refs`
- `policy_decision_refs`
- `observability_report_refs`
- `security_privacy_report_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `contract_only_refs`
- `missing_runtime_refs`
- `raw_prompt_leak_refs`
- `raw_response_leak_refs`
- `raw_credential_leak_refs`
- `provider_transcript_canonical_refs`
- `unsafe_tool_suggestion_refs`
- `unsupported_provider_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`

Pass validation requires all target provider families and no failure/review refs. `needs_review` requires contract-only or missing-runtime refs. `fail` requires failure details.

## ModelProviderAdapterFixtureManifest

Fixture manifest for deterministic CLI execution.

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`

Negative fixtures must expect `fail`; target profile is required.
