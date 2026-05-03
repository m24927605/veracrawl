# Data Model: Expanded Real-World Public Corpus Benchmark

## RealWorldQualityTargetSpec

- `id`: stable target id.
- `site_spec`: row 055 `RealWorldBenchmarkSiteSpec` used for live acquisition.
- `pattern_family_refs`: pattern families counted for quality coverage.
- `quality_tier`: `smoke`, `quality`, or `release`.
- `expected_quality_result`: expected target-level pass/fail for fixtures.

Validation:

- At least one `pattern_family_ref` is required.
- `quality_tier` must be declared in the parent manifest profile.
- `site_spec.pattern_refs` and `pattern_family_refs` must overlap or have an
  explicit mapping through stable refs.

## RealWorldQualityCorpusManifest

- `id`, `scenario`, `profile_refs`.
- `target_specs`: one or more `RealWorldQualityTargetSpec`.
- `allowed_origin_refs`: allowed public origins.
- `rate_budget_ref`.
- `minimum_target_count`, `minimum_origin_count`, `minimum_pattern_family_count`.
- `expected_completion_result`, `expected_operator_status`,
  `expected_failure_type`, `negative_case`.
- `required_ref_types`.

Validation:

- `quality` profile requires minimum thresholds >= 40 targets, 15 origins, and
  10 pattern families.
- Every target origin must be in `allowed_origin_refs`.
- Negative fixtures cannot expect `pass`.

## RealWorldQualitySiteObservation

- `id`, `target_spec_ref`, `site_observation_ref`, `target_url`.
- `pattern_family_refs`, `matched_observation_refs`.
- `policy_decision_refs`, `artifact_refs`, `content_hash_refs`,
  `canonical_url_refs`, `command_record_refs`, `event_cursor_refs`,
  `outbox_refs`, `replay_bundle_ref`.
- `failure_type`, `failure_report_refs`, `missing_ref_fields`, `diagnostics`.
- `completion_result`.

Validation:

- Passing quality observations require a passing row 055 site observation and all
  replay/evidence refs.
- Non-pass observations require typed diagnostics.

## RealWorldQualityPatternCoverageRecord

- `id`, `pattern_family_ref`.
- `declared_target_refs`, `passing_target_refs`, `failed_target_refs`.
- `site_observation_refs`, `quality_observation_refs`.
- `completion_result`.

Validation:

- A passing coverage record requires at least one passing target.
- Failed coverage records must include diagnostics.

## RealWorldQualityCorpusReport

- `id`, `fixture_id`, `run_ref`.
- `real_world_benchmark_run_report_ref`.
- `quality_observation_refs`, `pattern_coverage_refs`,
  `site_observation_refs`.
- `passing_target_count`, `declared_target_count`, `origin_count`,
  `pattern_family_count`.
- policy/network/drift/replay counters.
- `policy_decision_refs`, `artifact_refs`, `content_hash_refs`,
  `canonical_url_refs`, `command_record_refs`, `event_cursor_refs`,
  `outbox_refs`, `replay_bundle_refs`.
- `failure_type`, `failure_report_refs`, `missing_ref_fields`, `diagnostics`.
- `operator_status`, `completion_result`.

Validation:

- Passing reports require thresholds met, complete refs, no failure reports, and
  no missing replay refs.
- Non-pass reports require typed failure diagnostics.
