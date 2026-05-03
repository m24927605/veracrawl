# Data Model: JavaScript Browser Crawl Quality Benchmark

## BrowserQualityTargetSpec

Declares one browser-required target.

- `id`: stable target ref.
- `target_url`: public or fixture URL.
- `allowed_origin`: required egress origin.
- `robots_url`: robots preflight URL when used by live public validation.
- `http_absent_fragments`: fragments expected to be missing from HTTP-only
  evidence.
- `browser_required_fragments`: fragments that must be recovered from rendered
  DOM text.
- `pattern_refs`: browser/source pattern refs.
- `sandbox_policy_ref`: browser sandbox policy ref.
- `browser_budget_ref`: browser budget ref.
- `max_runtime_ms`: per-target browser timeout.
- `max_network_request_count`: request budget for browser observation.
- `expected_quality_result`: target-level expected result.

## BrowserQualityObservation

Records one target's HTTP-only and browser-rendered outcome.

- HTTP refs: live HTTP report, network response, raw artifact, content hash.
- Browser refs: browser step, DOM artifact, screenshot artifact, network trace,
  console log, timing artifact, rendered content hash.
- Differential refs: recovered fragment refs, missing HTTP fragment refs,
  source anchor refs, quality delta ref.
- Safety refs: sandbox policy, policy decisions, prompt-taint boundary, browser
  budget.
- Runtime refs: command records, event cursor, outbox, replay bundle.
- Metrics: wall time, network request count, blocked request count, browser cost
  units.
- Failure refs: typed failure, diagnostics, missing ref fields.

## BrowserQualityDeltaRecord

Represents the measurable quality gain for one target.

- `id`
- `target_spec_ref`
- `http_missing_fragment_refs`
- `browser_recovered_fragment_refs`
- `source_anchor_refs`
- `content_hash_refs`
- `quality_gain_count`
- `diagnostics`
- `completion_result`

## BrowserQualityReport

Aggregates target observations.

- `target_count`
- `browser_required_pass_count`
- `recovered_fragment_count`
- `http_only_missing_count`
- `budget_exceeded_count`
- `unsafe_blocked_count`
- `prompt_taint_blocked_count`
- `artifact_missing_count`
- `replay_missing_count`
- required refs across observations
- `completion_result`, `operator_status`, typed failure diagnostics

## BrowserQualityCorpusManifest

Defines quality benchmark inputs and expected result.

- `id`
- `scenario`
- `profile_refs`
- `target_specs`
- `minimum_browser_required_count`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`
- `required_ref_types`

## Validation Rules

- Passing targets require browser-only recovered fragments and source anchors.
- Passing observations require DOM, screenshot, network, console, timing,
  content hash, policy, command, event, outbox, and replay refs.
- Passing reports require at least eight browser-required passing targets.
- Non-pass observations and reports require typed failure diagnostics.
- Browser engine state must not be persisted in canonical VeraCrawl state.
