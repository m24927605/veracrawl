# Data Model: Browser Snapshot Runtime

## BrowserSnapshotRuntimeReport

- `id`, `fixture_id`, `run_ref`
- upstream refs: `live_http_acquisition_report_ref`,
  `structured_source_adapters_runtime_report_ref`,
  `source_acquisition_report_ref`
- browser refs: `sandbox_policy_ref`, `browser_step_ref`,
  `dom_artifact_refs`, `screenshot_artifact_refs`,
  `network_trace_refs`, `console_log_refs`, `timing_refs`,
  `browser_budget_refs`
- runtime refs: `artifact_refs`, `policy_decision_refs`,
  `command_record_refs`, `event_cursor_refs`, `outbox_refs`,
  `replay_bundle_ref`
- failure refs: `failure_report_refs`, `missing_ref_fields`,
  `failure_type`, `operator_status`, `completion_result`, `diagnostics`

Passing reports require all upstream, browser, runtime, and replay refs. Failed
reports require typed diagnostics.

## BrowserSnapshotFixtureManifest

- `id`, `scenario`, `path`, `profile_refs`
- expected completion/status/failure fields
- `negative_case`
- `required_ref_types`

Target fixtures must support the `target` profile and declare required ref
types. Negative fixtures must declare an expected failure type.

## BrowserSnapshotRuntimeResult

Runtime return object containing the canonical report and optional underlying
browser observation outcome. The result is not canonical state; it exists for
tests and CLI conversion.
