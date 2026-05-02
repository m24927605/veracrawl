# Data Model: VeraCrawl Advanced Graph Projection Spine

## ProjectionSpec

- `id`
- `run_ref`
- `projection_name`
- `input_manifest_refs`
- `graph_version`
- `rebuild_policy_ref`
- `owner_service_ref`
- `policy_decision_refs`

## ProjectionRebuildJob

- `id`
- `run_ref`
- `projection_spec_ref`
- `input_manifest_refs`
- `expected_rebuild_hash`
- `actual_rebuild_hash`
- `watermark_ref`
- `status`
- `policy_decision_refs`

## ProjectionMismatchReport

- `id`
- `run_ref`
- `projection_rebuild_job_ref`
- `expected_rebuild_hash`
- `actual_rebuild_hash`
- `mismatch_ref`
- `operator_status`

## GraphSignal

- `id`
- `run_ref`
- `signal_type`
- `subject_ref`
- `score`
- `source_graph_refs`
- `explanation_ref`
- `policy_decision_refs`
- `evidence_ref_allowed`

`evidence_ref_allowed` must remain false.

## GraphDeltaReport

- `id`
- `run_ref`
- `previous_manifest_ref`
- `current_manifest_ref`
- `added_node_refs`
- `removed_node_refs`
- `added_edge_refs`
- `removed_edge_refs`
- `changed_signal_refs`
- `rebuild_hash`

## GraphQualityReport

- `id`
- `run_ref`
- `graph_manifest_ref`
- `metric_refs`
- `score_refs`
- `warning_refs`
- `policy_decision_refs`

## TemporalGraphProjectionRecord

- `id`
- `run_ref`
- `source_output_refs`
- `valid_from_ref`
- `valid_to_ref`
- `entity_identity_ref`
- `evidence_packet_refs`
- `projection_watermark_ref`

## AdvancedGraphProjectionReport

- `id`
- `run_ref`
- `projection_spec_ref`
- `rebuild_job_ref`
- `delta_report_ref`
- `quality_report_ref`
- `signal_refs`
- `temporal_record_refs`
- `mismatch_report_ref`
- `watermark_ref`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `failure_report_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`

## AdvancedGraphFixtureManifest

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `negative_case`
