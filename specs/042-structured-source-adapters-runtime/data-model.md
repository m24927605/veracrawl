# Data Model: Structured Source Adapters Runtime

## StructuredSourceAdapterRecord

- `id`
- `adapter_type`
- `source_adapter_result_ref`
- `natural_result_refs`
- `artifact_refs`
- `metadata_refs`
- `evidence_seed_refs`
- `discovered_url_refs`
- `api_payload_refs`
- `document_artifact_refs`
- `file_artifact_refs`
- `fetch_attempt_refs`
- `fetch_result_refs`
- `page_snapshot_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_refs`
- `content_hash_refs`
- `failure_report_refs`
- `missing_ref_fields`
- `failure_type`
- `result`

## StructuredSourceAdaptersRuntimeReport

- `id`
- `fixture_id`
- `run_ref`
- `required_adapter_types`
- `verified_adapter_types`
- `source_adapter_record_refs`
- `source_adapter_result_refs`
- `natural_result_refs`
- `artifact_refs`
- `evidence_seed_refs`
- `discovered_url_refs`
- `api_payload_refs`
- `document_artifact_refs`
- `file_artifact_refs`
- `fetch_attempt_refs`
- `fetch_result_refs`
- `page_snapshot_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `failure_report_refs`
- `missing_ref_fields`
- `failure_type`
- `operator_status`
- `completion_result`
- `diagnostics`

## StructuredSourceAdaptersFixtureManifest

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`
- `required_ref_types`
