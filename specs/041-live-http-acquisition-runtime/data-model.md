# Data Model: Live HTTP Acquisition Runtime

## LiveHttpAcquisitionReport

- `id`
- `fixture_id`
- `run_ref`
- `run_control_report_ref`
- `production_persistence_report_ref`
- `network_request_ref`
- `network_response_ref`
- `redirect_hop_refs`
- `source_acquisition_report_ref`
- `source_adapter_result_refs`
- `fetch_attempt_refs`
- `fetch_result_refs`
- `page_snapshot_refs`
- `source_observation_refs`
- `artifact_refs`
- `content_hash_refs`
- `canonical_url_refs`
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

## LiveHttpFixtureManifest

- `id`
- `scenario`
- `path`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`
- `required_ref_types`

## TargetSourceObservationRecord

041 creates a source observation with content hash, source observation,
artifact, evidence seed, graph seed, policy, and replay refs for successful HTTP
acquisition.
