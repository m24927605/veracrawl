# Data Model: Credentialed Session Runtime

## CredentialedSessionRuntimeReport

- `id`, `fixture_id`, `run_ref`
- upstream refs: `live_http_acquisition_report_ref`,
  `browser_snapshot_runtime_report_ref`
- credential/session refs: `credential_scope_refs`, `authorized_origin_refs`,
  `approval_decision_refs`, `credential_use_audit_refs`,
  `session_adapter_result_refs`, `session_state_refs`
- redaction/replay refs: `redaction_map_refs`, `redacted_artifact_refs`,
  `redacted_replay_refs`, `replay_bundle_ref`
- runtime refs: `policy_decision_refs`, `command_record_refs`,
  `event_cursor_refs`, `outbox_refs`
- failure refs: `failure_report_refs`, `missing_ref_fields`, `failure_type`,
  `raw_secret_leak_refs`, `adapter_native_state_canonical_refs`,
  `operator_status`, `completion_result`, `diagnostics`

Passing reports require all upstream, credential/session, redaction, replay, and
runtime refs. Failed reports require typed diagnostics.

## CredentialedSessionFixtureManifest

- `id`, `scenario`, `path`, `profile_refs`
- expected completion/status/failure fields
- `negative_case`
- `required_ref_types`

Target fixtures must support the `target` profile and declare required refs.
Negative fixtures must declare an expected failure type.
