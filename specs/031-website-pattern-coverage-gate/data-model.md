# Data Model: Target Website Pattern Coverage Gate

## WebsitePatternCoverageRecord

- `id`
- `run_ref`
- `website_pattern`
- `benchmark_fixture_ref`
- `source_adapter_refs`
- `source_evidence_refs`
- `site_model_refs`
- `page_type_refs`
- `expected_output_oracle_refs`
- `evidence_coverage_refs`
- `policy_decision_refs`
- `artifact_oracle_refs`
- `event_oracle_refs`
- `graph_oracle_refs`
- `pattern_specific_refs`
- `safety_refs`
- `diagnostic_single_site_refs`
- `scaffold_only_refs`
- `unsupported_pattern_refs`
- `unsafe_interaction_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `missing_ref_fields`
- `result`

Validation:

- Pass requires source adapter, source evidence, site model/page type, output
  oracle, evidence coverage, policy, artifact oracle, command, event cursor,
  outbox, replay, and every type-specific ref declared for that pattern.
- Single-site diagnostic refs, scaffold-only refs, unsupported pattern refs, and
  unsafe interaction refs cannot be present on pass.

## WebsitePatternCoverageReport

- `coverage_record_refs`
- `covered_patterns`
- `missing_patterns`
- `unsupported_pattern_refs`
- `single_site_assumption_refs`
- `scaffold_only_refs`
- `unsafe_interaction_refs`
- `missing_pattern_specific_refs`
- `missing_replay_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `contract_only_refs`
- `missing_runtime_refs`
- `failure_type`
- `failure_report_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`

Validation:

- Pass requires coverage records for all 12 target website patterns and no
  missing/failure refs.
- Needs-review requires contract-only or missing-runtime refs.
- Fail requires typed failure details.

## WebsitePatternCoverageFixtureManifest

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`

Validation:

- Target profile is required.
- Negative fixtures cannot expect pass.
- Expected failure type requires negative case.
