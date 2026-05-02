# Data Model: Source Adapter and Fetch Runtime

## FetchAttempt

- **Owner**: `fetch`
- **Fields**: `id`, `run_ref`, `frontier_item_ref`, `lease_ref`, `adapter_spec_ref`, `source_ref`, `policy_decision_refs`, `attempt_number`, `status`, `retry_after_ref`, `failure_report_ref`
- **Validation**: non-success status requires policy, retry, or failure refs; attempt number must be positive.

## FetchResult

- **Owner**: `fetch`
- **Fields**: `id`, `attempt_ref`, `source_ref`, `status`, `result_type`, `raw_artifact_refs`, `metadata_refs`, `failure_report_ref`
- **Validation**: success requires raw artifact refs; blocked/failed requires failure refs.

## PageSnapshot

- **Owner**: `fetch`
- **Fields**: `id`, `fetch_result_ref`, `source_ref`, `raw_artifact_ref`, `content_digest`, `content_type`, `canonical_ref`, `privacy_classification_ref`
- **Validation**: digest and raw artifact refs are required.

## DocumentArtifact

- **Owner**: `fetch`
- **Fields**: `id`, `fetch_result_ref`, `source_ref`, `raw_artifact_ref`, `document_type`, `content_digest`, `metadata_refs`
- **Validation**: document type and raw artifact refs are required.

## RateLimitDecision

- **Owner**: `policy`
- **Fields**: `id`, `run_ref`, `source_ref`, `decision`, `retry_after_ref`, `rate_limit_policy_ref`, `reason_refs`
- **Validation**: rate-limited decisions require retry-after and reason refs.

## SourceFailureReport

- **Owner**: `fetch`
- **Fields**: `id`, `run_ref`, `source_ref`, `failure_type`, `operator_status`, `policy_decision_refs`, `retry_refs`, `diagnostic_refs`
- **Validation**: every failure report requires operator-visible status and diagnostics.

## SourceAcquisitionReport

- **Owner**: `fetch`
- **Fields**: `id`, `run_ref`, `source_adapter_result_ref`, `fetch_attempt_refs`, `fetch_result_refs`, `artifact_refs`, `policy_decision_refs`, `frontier_item_ref`, `lease_ref`, `command_record_refs`, `event_cursor_refs`, `outbox_refs`, `recovery_report_refs`, `missing_ref_fields`, `completion_result`
- **Validation**: pass requires source result, artifact, policy, command, event cursor, outbox, frontier, lease, and recovery refs with no missing refs.
