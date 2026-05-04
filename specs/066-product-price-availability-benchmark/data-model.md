# Data Model: Product Price Availability Benchmark

## ProductAvailabilityBenchmarkManifest

Fields:

- `id`, `scenario`, `profile_refs`.
- `product_name`, `brand`, `required_identity_terms`,
  `rejected_identity_terms`.
- `target_specs`: list of `ProductAvailabilityTargetSpec`.
- `provider_names`, `framework_names`.
- `expected_completion_result`, `expected_operator_status`,
  `expected_failure_type`, `negative_case`.
- `required_ref_types`.

Validation:

- Must support `target` profile.
- Must include at least one target.
- Must declare product identity terms.
- Negative manifests cannot expect pass.

## ProductAvailabilityTargetSpec

Fields:

- `id`, `site_name`, `target_url`, `robots_url`, `allowed_origin`.
- `expected_status_code`, `expected_content_type`.
- `required_identity_terms`, `rejected_identity_terms`.
- `allowed_robots_status_codes`, `timeout_ms`, `size_budget_bytes`.
- `expected_site_result`: `pass`, `fail`, or `needs_review`.

Validation:

- URLs must be absolute http(s) and same-origin.
- Private-network targets are rejected.
- Passing targets require identity, price, availability, source evidence, and AI
  traces.

## ProductAvailabilityFieldEvidence

Fields:

- `field_name`: `identity`, `price`, or `availability`.
- `raw_text`, `normalized_value`, `currency`, `amount`.
- `source_anchor_ref`, `artifact_ref`, `content_hash_ref`,
  `canonical_url_ref`.
- `model_call_trace_ref`, `agent_action_trace_ref`, `tool_call_trace_refs`,
  `context_bundle_trace_ref`.
- `evidence_packet_ref`, `verification_decision_ref`.
- `policy_decision_refs`, `command_record_refs`, `event_cursor_refs`,
  `outbox_refs`, `replay_bundle_ref`.

Validation:

- Passing field evidence requires source refs and replay refs.
- `artifact_ref` may refer to an HTTP artifact or read-only browser DOM artifact
  depending on the run mode.
- Price evidence requires raw text and either amount or normalized value.
- Availability evidence requires a normalized availability status.

## ProductAvailabilitySiteResult

Fields:

- Target and live HTTP refs.
- `field_evidence_refs`.
- Optional `identity_evidence_ref`, `price_evidence_ref`,
  `availability_evidence_ref`.
- AI trace refs, evidence refs, policy refs, command/event/outbox refs, replay
  refs.
- `failure_type`, `diagnostics`, `completion_result`.

Validation:

- Pass requires identity, price, availability, source/evidence/replay refs, and
  AI trace refs.
- Non-pass requires typed diagnostics.

## ProductAvailabilityBenchmarkReport

Fields:

- `site_result_refs`, `passing_site_result_refs`, `blocked_site_result_refs`.
- `field_evidence_refs`, AI trace refs, evidence refs, command/event/outbox
  refs, replay refs.
- `completion_result`: pass only when all required sites pass; needs-review when
  some source-backed results pass and some sites are blocked; fail when no
  source-backed fields pass or validation contracts are violated.
