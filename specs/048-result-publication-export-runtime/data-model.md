# Data Model: Result Publication And Export Runtime

## ResultApiSnapshot

- `id`
- `run_ref`
- `published_output_refs`
- `output_manifest_refs`
- `response_artifact_ref`
- `response_schema_ref`
- `privacy_lifecycle_refs`
- `replay_bundle_ref`
- `response_hash`

Pass validation requires output refs, manifest refs, response artifact/hash,
privacy lifecycle, and replay refs.

## ResultPublicationExportRuntimeReport

- row 047 live evidence refs
- extraction candidate refs
- evidence coverage/packet/manifest refs
- verification and review refs
- publication report refs
- published output and output manifest refs
- Result API snapshot refs
- export target/job/attempt/delivery receipt refs
- withdrawal job/attempt refs
- correction record refs
- destination object mapping refs
- policy/privacy refs
- command/event/outbox refs
- replay refs
- typed failure diagnostics

Pass validation rejects missing refs, typed failures, missing-ref diagnostics,
or direct export bypass markers.

## ResultPublicationExportFixtureManifest

- fixture id/scenario/profile
- source path and schema ref for prerequisite chain
- expected completion result/status/failure type
- required ref types

Negative fixtures require a non-pass expected result and a typed failure.
