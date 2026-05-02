# Data Model: VeraCrawl Normalize and Extract Plane

## NormalizationManifest

- `id`
- `run_ref`
- `raw_artifact_ref`
- `normalized_artifact_ref`
- `anchor_map_ref`
- `parser_ref`
- `transformation_version`
- `input_digest`
- `output_digest`
- `policy_decision_refs`

## TextAnchor

- `id`
- `normalized_document_ref`
- `raw_artifact_ref`
- `label`
- `text`
- `normalized_start`
- `normalized_end`
- `selector_ref`

## AnchorMap

- `id`
- `normalized_document_ref`
- `raw_artifact_ref`
- `anchor_refs`
- `content_digest`

## LinkProvenance

- `id`
- `normalized_document_ref`
- `source_url_ref`
- `href`
- `anchor_text`
- `anchor_ref`
- `policy_decision_refs`
- `status`

## PageTypeClassification

- `id`
- `normalized_document_ref`
- `page_type`
- `signal_refs`
- `confidence_ref`

## SiteModel

- `id`
- `run_ref`
- `page_type_refs`
- `link_provenance_refs`
- `canonical_url_refs`
- `summary_ref`

## ExtractionStrategy

- `id`
- `run_ref`
- `schema_ref`
- `normalized_document_refs`
- `field_names`
- `strategy_type`
- `policy_decision_refs`

## NormalizeExtractReport

- `id`
- `run_ref`
- `network_acquisition_report_ref`
- `normalized_document_ref`
- `normalization_manifest_ref`
- `anchor_map_ref`
- `link_provenance_refs`
- `page_type_classification_ref`
- `site_model_ref`
- `extraction_strategy_ref`
- `extraction_candidate_ref`
- `artifact_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `failure_report_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`
