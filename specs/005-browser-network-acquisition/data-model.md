# Data Model: VeraCrawl Browser and Network Acquisition Runtime

## NetworkRequest

- `id`
- `run_ref`
- `source_ref`
- `url`
- `method`
- `headers_ref`
- `policy_decision_refs`
- `egress_policy_ref`
- `private_network_policy_ref`
- `robots_policy_ref`
- `rate_budget_ref`
- `size_budget_bytes`
- `timeout_ms`
- `idempotency_key`

Validation:

- URL must be absolute `http` or `https`.
- Method is read-only for this slice: `GET` or `HEAD`.
- Policy decision refs are required.
- Size and timeout budgets must be positive.

## RedirectHop

- `id`
- `request_ref`
- `sequence`
- `from_url`
- `to_url`
- `status_code`
- `policy_decision_refs`

Validation:

- Sequence starts at one.
- `from_url` and `to_url` must be absolute URLs.
- Redirect hops require policy refs.

## NetworkResponse

- `id`
- `request_ref`
- `status_code`
- `final_url`
- `headers_ref`
- `raw_artifact_ref`
- `content_digest`
- `content_type`
- `body_size_bytes`
- `redirect_hop_refs`
- `timing_ref`

Validation:

- Successful response requires raw artifact ref, content digest, content type, and non-negative body size.
- Redirect hop refs must be present when final URL differs from request URL.

## NetworkAcquisitionReport

- `id`
- `run_ref`
- `network_request_ref`
- `network_response_ref`
- `redirect_hop_refs`
- `browser_step_ref`
- `source_acquisition_report_ref`
- `artifact_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `recovery_report_refs`
- `failure_report_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`

Validation:

- Passing reports require request, response or browser step, source acquisition report, artifacts, policies, commands, event cursors, outbox refs, and recovery reports.
- Non-pass reports require failure refs or missing refs.

## BrowserSandboxPolicy

- `id`
- `allowed_origin_refs`
- `egress_allowlist`
- `private_network_denylist`
- `max_runtime_ms`
- `max_dom_bytes`
- `max_screenshot_bytes`
- `max_network_log_bytes`
- `allowed_side_effect_classes`
- `capture_dom`
- `capture_screenshot`
- `capture_network_log`

Validation:

- Budgets must be positive.
- Read-only side effects must be allowed for read-only browser observation.
- Empty egress allowlist is invalid for pass-capable browser observation.

## BrowserInteractionStep

- `id`
- `run_ref`
- `source_ref`
- `target_url`
- `step_number`
- `action_type`
- `side_effect_class`
- `sandbox_policy_ref`
- `policy_decision_refs`
- `dom_artifact_ref`
- `screenshot_artifact_ref`
- `network_log_ref`
- `status`
- `failure_report_ref`

Validation:

- Executed read-only steps require DOM, screenshot, and network log refs.
- Blocked or failed steps require a failure report ref.
- Unsafe side-effect classes cannot be executed in this slice.

## State Transitions

- Network acquisition: `planned -> executed -> reported`
- Blocked network acquisition: `planned -> blocked -> reported`
- Browser step: `planned -> executed | blocked | failed`
- Replay: `unchecked -> pass | fail | needs_review`

Illegal transitions:

- blocked network acquisition cannot later accept raw artifacts in the same report
- unsafe browser step cannot become executed without a future explicit approval policy
- pass report cannot contain missing replay refs
