# Contract: Result Publication And Export Runtime

## Command Types

- `record_result_api_snapshot`
- `record_result_publication_export_runtime_report`
- `record_result_publication_export_fixture_manifest`

## Event Types

- `result_api_snapshot_recorded`
- `result_publication_export_runtime_reported`
- `result_publication_export_fixture_manifest_recorded`

## Runtime Pass Requirements

A `ResultPublicationExportRuntimeReport` with `completion_result=pass` must
contain:

- live evidence runtime report ref
- candidate refs
- evidence coverage, packet, and manifest refs
- verification and review decision refs
- publication report refs
- published output refs
- output manifest refs
- Result API snapshot refs
- export target, job, attempt, receipt refs
- withdrawal and correction refs
- destination object mapping refs
- policy and privacy lifecycle refs
- command, event cursor, and outbox refs
- replay bundle ref

No pass report may include failure type, failure refs, missing refs, or direct
export bypass diagnostics.
