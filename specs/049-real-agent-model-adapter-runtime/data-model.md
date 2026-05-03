# Data Model: Real Agent And Model Adapter Runtime

## AgentModelAdapterRuntimeReport

Purpose: aggregate proof that row 049 executed agent/model adapter bindings for
planning, extraction, and repair while preserving canonical VeraCrawl state.

Fields:

- `id`, `fixture_id`, `run_ref`
- `run_control_report_ref`
- `live_normalization_runtime_report_ref`
- `schema_extraction_runtime_report_ref`
- `planning_agent_run_refs`
- `extraction_agent_run_refs`
- `repair_agent_run_refs`
- `provider_execution_refs`
- `framework_execution_refs`
- `requested_provider_names`, `verified_provider_names`
- `requested_framework_names`, `verified_framework_names`
- `model_request_refs`, `model_response_refs`, `model_call_trace_refs`
- `agent_run_request_refs`, `agent_run_result_refs`, `agent_action_trace_refs`
- `tool_call_trace_refs`, `context_bundle_trace_refs`
- `adapter_runtime_refs`, `adapter_availability_refs`
- `policy_decision_refs`, `observability_report_refs`,
  `security_privacy_report_refs`
- `command_record_refs`, `event_cursor_refs`, `outbox_refs`,
  `replay_bundle_ref`
- failure fields: `unavailable_runtime_refs`, `unsupported_provider_refs`,
  `unsupported_framework_refs`, `raw_prompt_leak_refs`,
  `raw_response_leak_refs`, `raw_credential_leak_refs`,
  `framework_state_canonical_refs`, `provider_transcript_canonical_refs`,
  `core_import_violation_refs`, `failure_report_refs`,
  `missing_ref_fields`, `failure_type`, `diagnostics`
- `operator_status`, `completion_result`

Validation rules:

- `pass` requires all upstream refs, planning/extraction/repair refs, provider
  and framework execution refs, model/context/tool/action traces, policy,
  observability, security/privacy, command/event/outbox, adapter runtime, and
  replay refs.
- `pass` rejects raw prompt/response/credential leakage, canonical
  framework/provider-native state, unsupported provider/framework refs, external
  runtime unavailability, core import violations, and missing ref fields.
- `needs_review` requires unavailable runtime refs or adapter availability refs.
- `fail` requires a typed `failure_type` and concrete failure refs or missing
  fields.

## AgentModelAdapterFixtureManifest

Purpose: fixture declaration for row 049 CLI/integration tests.

Fields:

- `id`
- `scenario`
- `profile_refs`
- `provider_names`
- `framework_names`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`

Validation rules:

- `profile_refs` must include `target`.
- Negative cases must expect `fail` or `needs_review`.
- `expected_failure_type` requires a negative case.

## Adapter Runtime Bindings

Runtime bindings are dataclasses in `veracrawl.agents.real_adapter_runtime`, not
canonical Pydantic contracts.

Fields:

- provider binding: `provider_name`, `model_id`, `model_version`,
  `runtime_ref`, `adapter_module_ref`, `port`
- framework binding: `framework_name`, `runtime_spec_id`, `runtime_ref`,
  `adapter_module_ref`, `port`

Rules:

- Bindings are runtime wiring only; they are not persisted as canonical state.
- Canonical persistence records only the generated request/result/trace refs and
  diagnostic adapter refs.
