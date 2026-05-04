# Data Model: Query Product Discovery And Offer Ranking

## ProductDiscoverySourceSpec

- `id`
- `site_name`
- `search_url`
- `robots_url`
- `allowed_origin`
- `query`
- `required_identity_terms`
- `rejected_identity_terms`
- `candidate_url_patterns`
- `exclude_url_patterns`
- `max_candidates`
- `timeout_ms`
- `size_budget_bytes`
- `allowed_robots_status_codes`
- `expected_source_result`

Validation:

- Search and robots URLs must be absolute HTTP(S), public-network URLs.
- Search URL and robots URL origins must match `allowed_origin`.
- Query and required identity terms are mandatory.
- Candidate limits and budgets must be positive.

## ProductDiscoveryCandidate

- `id`
- `fixture_id`
- `source_spec_ref`
- `site_name`
- `query`
- `search_url`
- `candidate_url`
- `candidate_rank`
- `raw_anchor_text`
- `matched_identity_terms`
- `source_anchor_ref`
- `artifact_ref`
- `content_hash_ref`
- `canonical_url_ref`
- `model_call_trace_ref`
- `agent_action_trace_ref`
- `tool_call_trace_refs`
- `context_bundle_trace_ref`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `completion_result`

Validation:

- Passing candidates require source, trace, policy, command/event/outbox, and
  replay refs.
- LLM output refs cannot appear as source evidence.

## ProductDiscoveryRunReport

- `id`
- `fixture_id`
- `run_ref`
- `query`
- `product_name`
- `source_count`
- `source_result_refs`
- `discovered_candidate_refs`
- `accepted_candidate_refs`
- `blocked_source_refs`
- `derived_product_availability_manifest_ref`
- `product_availability_report_ref`
- `offer_projection_report_ref`
- `ranked_offer_refs`
- `model_call_trace_refs`
- `agent_action_trace_refs`
- `tool_call_trace_refs`
- `context_bundle_trace_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_refs`
- `operator_status`
- `completion_result`
- `diagnostics`

Validation:

- Passing reports require candidates, composed product availability refs, offer
  projection refs, traces, policy refs, command/event/outbox refs, and replay
  refs.
- Needs-review reports require at least one useful result or typed diagnostics.

## ProductDiscoveryBenchmarkManifest

- `id`
- `scenario`
- `profile_refs`
- `product_name`
- `brand`
- `query`
- `required_identity_terms`
- `rejected_identity_terms`
- `source_specs`
- `max_total_candidates`
- `ranking_limit`
- `provider_names`
- `framework_names`
- `expected_completion_result`
- `expected_operator_status`
- `required_ref_types`
- `negative_case`

Validation:

- Must support `target` profile.
- Must declare search/listing sources, not product target specs.
- Required refs must include discovery, AI trace, source anchor, command/event/
  outbox, replay, product availability, and offer projection coverage.
