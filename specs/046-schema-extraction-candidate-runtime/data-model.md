# Data Model: Schema Extraction Candidate Runtime

## SchemaExtractionRuntimeReport

- `id`, `fixture_id`, `run_ref`
- upstream refs: `live_normalization_runtime_report_ref`
- normalized refs: `normalized_document_refs`, `source_anchor_refs`,
  `anchor_map_refs`
- extraction refs: `extraction_strategy_refs`, `extraction_candidate_refs`,
  `candidate_field_anchor_refs`, `confidence_refs`
- schema refs: `schema_refs`, `schema_validation_refs`,
  `approved_exploratory_schema_refs`
- framework-neutral trace refs: `model_trace_refs`, `tool_trace_refs`
- review refs: `candidate_rejection_refs`, `drift_signal_refs`,
  `repair_recommendation_refs`
- runtime refs: `artifact_refs`, `policy_decision_refs`,
  `command_record_refs`, `event_cursor_refs`, `outbox_refs`,
  `replay_bundle_ref`
- forbidden output refs: `publication_refs`
- failure refs: `failure_report_refs`, `missing_ref_fields`,
  `failure_type`, `operator_status`, `completion_result`, `diagnostics`

Passing reports require all upstream, normalized, extraction, schema, trace,
runtime, and replay refs and must have no publication refs. Failed or
needs-review reports require typed diagnostics.

## SchemaExtractionFixtureManifest

- `id`, `scenario`, `path`, `profile_refs`
- `schema_ref`
- `approved_exploratory_schema`
- expected completion/status/failure fields
- `negative_case`
- `required_ref_types`
