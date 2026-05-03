# Data Model: Dynamic Source Adapter Runtime Foundation

## DynamicSourceRuntimeAdapterRecord

- `adapter_type`: required source adapter family.
- `source_adapter_result_ref`: canonical `SourceAdapterResult`.
- `natural_result_refs`: adapter-native result refs.
- `fetch_attempt_refs`, `page_snapshot_refs`, `browser_interaction_refs`, `credential_audit_refs`, `document_artifact_refs`, `api_payload_refs`, `file_artifact_refs`, `seed_plan_refs`, `prior_snapshot_refs`: adapter-specific refs.
- `command_result_refs`, `policy_decision_refs`, `observability_report_refs`, `security_privacy_report_refs`, `replay_bundle_ref`: operational envelope refs.
- `live_runtime_refs`, `contract_adapter_refs`, `diagnostic_adapter_state_refs`: runtime availability and adapter diagnostics.
- `raw_secret_persisted`, `adapter_native_state_canonical`, `unsafe_browser_side_effect_refs`: hard failure fields.
- `missing_ref_fields`, `result`: completeness state.

## DynamicSourceRuntimeReport

- Aggregates all adapter runtime records.
- `pass` requires every required adapter family and all aggregate runtime, command, policy, observability, security/privacy, event/outbox, and replay refs.
- `needs_review` requires missing runtime or contract-only refs.
- `fail` requires failure details.

## DynamicSourceRuntimeFixtureManifest

- Declares scenario, target profile, expected completion result, operator status, expected failure type, and negative case flag.
