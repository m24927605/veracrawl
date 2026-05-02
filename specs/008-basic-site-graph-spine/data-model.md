# Data Model: VeraCrawl Basic Site Graph Spine

## GraphNode

- `id`
- `run_ref`
- `node_key`
- `node_type`
- `label`
- `source_ref`
- `property_refs`

## GraphEdge

- `id`
- `run_ref`
- `from_node_ref`
- `to_node_ref`
- `edge_type`
- `provenance_ref`
- `property_refs`

## GraphEdgeProvenance

- `id`
- `edge_ref`
- `input_refs`
- `policy_decision_refs`
- `evidence_ref_allowed`

## ProjectionWatermark

- `id`
- `projection_ref`
- `input_manifest_ref`
- `event_cursor_refs`
- `rebuild_hash`
- `freshness_ref`

## GraphBuildManifest

- `id`
- `run_ref`
- `input_refs`
- `graph_version`
- `node_refs`
- `edge_refs`
- `provenance_refs`
- `watermark_ref`
- `policy_decision_refs`
- `rebuild_hash`

## GraphBuildReport

- `id`
- `run_ref`
- `manifest_ref`
- `node_refs`
- `edge_refs`
- `provenance_refs`
- `watermark_ref`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `failure_report_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`

## GraphFixtureManifest

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `negative_case`
