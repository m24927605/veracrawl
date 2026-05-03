# Data Model: Target Output Type Coverage Gate

## OutputTypeCoverageRecord

- `id`
- `run_ref`
- `output_type`
- `candidate_ref`
- `published_output_ref`
- `output_manifest_ref`
- `evidence_packet_ref`
- `evidence_coverage_ref`
- `verification_decision_ref`
- `publication_policy_refs`
- `source_evidence_refs`
- `field_evidence_refs`
- `type_specific_refs`
- `privacy_lifecycle_refs`
- `artifact_refs`
- `diagnostic_graph_refs`
- `diagnostic_memory_refs`
- `diagnostic_agent_reasoning_refs`
- `diagnostic_temporal_kg_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `result`

Validation:

- Pass requires source evidence, evidence coverage, verification, publication, manifest, lifecycle, command, event cursor, outbox, and replay refs.
- Pass requires every type-specific ref declared for that output type.
- Derived diagnostic refs cannot replace source evidence.

## OutputTypePublicationGateReport

- `coverage_record_refs`
- `covered_output_types`
- `missing_output_types`
- `unsupported_output_type_refs`
- `derived_context_as_evidence_refs`
- `missing_type_specific_refs`
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

- Pass requires coverage records for all seven target output types and no missing/failure refs.
- Needs-review requires contract-only or missing-runtime refs.
- Fail requires typed failure details.

## OutputTypeCoverageFixtureManifest

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
