# Data Model: Agent Runtime Adapter Operational Gate

## AgentAdapterExecutionRecord

- `id`
- `framework_name`
- `runtime_spec_ref`
- `agent_run_request_ref`
- `agent_run_result_ref`
- `agent_action_trace_ref`
- `model_call_trace_refs`
- `tool_call_trace_refs`
- `context_bundle_trace_ref`
- `command_result_refs`
- `policy_decision_refs`
- `observability_report_refs`
- `security_privacy_report_refs`
- `replay_bundle_ref`
- `live_runtime_refs`
- `contract_adapter_refs`
- `diagnostic_framework_state_refs`
- `raw_prompt_persisted`
- `raw_response_persisted`
- `framework_state_canonical`
- `missing_ref_fields`
- `result`

Validation:

- `pass` requires request/result/action/context/replay/policy/observability/security refs, model and tool trace refs, and either live runtime refs or contract adapter refs.
- raw prompt/response persistence is forbidden.
- framework-native state cannot be canonical.

## AgentRuntimeAdapterReport

- `id`
- `run_ref`
- `framework_execution_refs`
- `required_framework_names`
- `verified_framework_names`
- `model_provider_refs`
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
- `framework_state_canonical_refs`
- `unsupported_framework_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`

Validation:

- `pass` requires all required frameworks verified and all canonical refs present.
- `needs_review` requires contract-only or missing-runtime refs.
- `fail` requires explicit failure refs or missing fields.

## AgentRuntimeAdapterFixtureManifest

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`

Validation:

- target profile is mandatory.
- negative fixtures must expect `fail`.
