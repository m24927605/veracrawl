# Data Model: Real-World Benchmark Corpus Gate

## RealWorldBenchmarkCorpusManifest

- `id`: corpus fixture id.
- `scenario`: benchmark scenario.
- `profile_refs`: supported profiles; must include `target`.
- `site_specs`: one or more `RealWorldBenchmarkSiteSpec`.
- `allowed_origin_refs`: explicit origins permitted for the run.
- `rate_budget_ref`: declared rate budget reference.
- `expected_completion_result`: aggregate expected completion result.
- `expected_operator_status`: expected aggregate operator status.
- `expected_failure_type`: optional failure type for negative corpus fixtures.
- `negative_case`: true for negative fixtures.
- `required_ref_types`: ref categories required for a pass.

Validation:

- `target` profile is required.
- At least one site spec is required.
- Every site origin must appear in `allowed_origin_refs`.
- Negative fixtures cannot expect pass and must declare failure type.

## RealWorldBenchmarkSiteSpec

- `id`: stable site id.
- `target_url`: absolute HTTP(S) URL.
- `robots_url`: absolute same-origin robots URL.
- `allowed_origin`: exact scheme/host/port origin.
- `expected_status_code`: expected HTTP status code.
- `expected_content_type`: expected response content type prefix.
- `min_body_size_bytes`: minimum response body size.
- `required_title_fragments`: fragments that must appear in the HTML title.
- `required_body_fragments`: fragments that must appear in the body.
- `required_regex_counts`: map of regex pattern to minimum count.
- `allowed_robots_status_codes`: robots response statuses that may proceed.
- `timeout_ms`, `size_budget_bytes`: per-site acquisition budgets.
- `pattern_refs`: declared target website pattern refs represented by this site.

Validation:

- target and robots URLs must be absolute HTTP(S).
- target and robots origins must match `allowed_origin`.
- budgets and expected sizes must be positive.
- private-network URLs are rejected before acquisition.

## RealWorldBenchmarkSiteObservation

- `id`: observation id.
- `site_spec_ref`: site spec id.
- `target_url`: fetched target URL.
- `robots_policy_ref`: robots policy decision ref.
- `live_http_report_ref`: live HTTP acquisition report id.
- `network_response_ref`: network response ref.
- `source_observation_refs`, `artifact_refs`, `content_hash_refs`, `canonical_url_refs`: evidence refs.
- `policy_decision_refs`, `command_record_refs`, `event_cursor_refs`, `outbox_refs`: replay-critical refs.
- `replay_bundle_ref`: live HTTP replay bundle ref.
- `status_code`, `content_type`, `body_size_bytes`, `content_digest`: observed response metadata.
- `matched_observation_refs`: matched oracle refs.
- `failure_report_refs`, `missing_ref_fields`, `failure_type`, `diagnostics`: non-pass diagnostics.
- `completion_result`: pass/fail/needs_review.

Validation:

- Passing observations require all evidence and replay refs.
- Non-pass observations require typed diagnostics.

## RealWorldBenchmarkRunReport

- `id`: aggregate report id.
- `fixture_id`: corpus id.
- `run_ref`: aggregate benchmark run ref.
- `site_observation_refs`: observation ids.
- `live_http_report_refs`: live HTTP report ids.
- `network_response_refs`: network response refs.
- `source_observation_refs`, `artifact_refs`, `content_hash_refs`, `canonical_url_refs`: aggregate evidence refs.
- `policy_decision_refs`, `command_record_refs`, `event_cursor_refs`, `outbox_refs`: aggregate replay refs.
- `replay_bundle_refs`: aggregate replay bundle refs.
- `benchmark_corpus_ref`: corpus manifest ref.
- `benchmark_run_refs`: per-site benchmark run refs.
- `failure_report_refs`, `missing_ref_fields`, `failure_type`, `diagnostics`: non-pass diagnostics.
- `operator_status`, `completion_result`: aggregate outcome.

Validation:

- Passing reports require all site observations and aggregate evidence/replay refs.
- Passing reports cannot include failure refs, missing refs, or failure type.
- Non-pass reports require a typed failure and diagnostics.
