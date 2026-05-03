# Data Model: Live Normalization And Site Understanding

## LiveNormalizationRuntimeReport

- `id`, `fixture_id`, `run_ref`
- upstream refs: `live_http_acquisition_report_ref`,
  `structured_source_adapters_runtime_report_ref`,
  `browser_snapshot_runtime_report_ref`
- processing refs: `normalized_document_refs`, `normalization_manifest_refs`,
  `anchor_map_refs`, `source_anchor_refs`, `link_provenance_refs`,
  `link_analysis_refs`, `page_type_classification_refs`, `site_model_refs`
- runtime refs: `raw_artifact_refs`, `normalized_artifact_refs`,
  `artifact_refs`, `policy_decision_refs`, `command_record_refs`,
  `event_cursor_refs`, `outbox_refs`, `replay_bundle_ref`
- failure refs: `failure_report_refs`, `missing_ref_fields`, `failure_type`,
  `operator_status`, `completion_result`, `diagnostics`

Passing reports require all upstream refs, normalized refs, anchor refs,
link-analysis refs, page type refs, site model refs, policy refs, runtime refs,
and replay refs. `link_provenance_refs` are required only when the normalized
page contains outbound links; linkless pages record a deterministic no-link
analysis ref. Failed reports require typed diagnostics.

## LiveNormalizationFixtureManifest

- `id`, `scenario`, `path`, `profile_refs`
- expected completion/status/failure fields
- `negative_case`
- `required_ref_types`
