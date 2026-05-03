# Data Model: Temporal KG Identity Projection Gate

## TemporalKGEntityIdentity

- `id`
- `run_ref`
- `entity_key`
- `entity_type`
- `canonical_label`
- `alias_refs`
- `identity_evidence_refs`
- `source_verified_fact_refs`
- `source_published_output_refs`
- `source_event_refs`
- `confidence`
- `valid_from_ref`
- `valid_to_ref`
- `transaction_time_ref`
- `status`
- `provisional_graph_identity_refs`
- `conflict_record_refs`
- `adjudication_record_refs`
- `supersedes_identity_ref`
- `superseded_by_identity_ref`
- `invalidation_ref`

Validation:

- Identity key, type, label, evidence refs, valid-from ref, transaction-time ref, and canonical source refs are required.
- Current identities cannot include provisional graph identity refs.
- Invalidated identities require adjudication and invalidation refs.
- Superseded identities require supersession refs.

## TemporalKGProjectionRecord

- `id`
- `run_ref`
- `projection_version`
- `entity_identity_ref`
- `subject_entity_key`
- `predicate`
- `object_value_ref`
- `object_entity_key`
- `value_type`
- `valid_from_ref`
- `valid_to_ref`
- `observed_at_ref`
- `projected_at_ref`
- `superseded_at_ref`
- `source_verified_fact_refs`
- `source_published_output_refs`
- `source_event_refs`
- `evidence_packet_refs`
- `conflict_record_refs`
- `supersedes_projection_record_ref`
- `status`
- `projection_watermark_ref`
- `evidence_ref_allowed`

Validation:

- Entity identity, subject, predicate, object value, value type, valid time, transaction time, source refs, evidence refs, and watermark refs are required.
- Temporal KG projection records cannot be marked as source evidence.
- Superseded records require supersession transaction refs.

## TemporalKGIdentityAdjudicationRecord

- `id`
- `run_ref`
- `conflict_type`
- `decision_type`
- `identity_refs`
- `projection_record_refs`
- `conflict_record_refs`
- `adjudication_authority_ref`
- `evidence_input_refs`
- `source_event_refs`
- `policy_decision_refs`
- `resulting_identity_refs`
- `resulting_projection_record_refs`
- `invalidated_identity_refs`
- `superseded_identity_refs`
- `superseded_projection_record_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `result`

Validation:

- Conflict, decision, authority, evidence, source event, policy, command, event cursor, outbox, and replay refs are required.
- False-merge adjudication requires invalidation or supersession refs.
- False-split adjudication requires resulting identity refs and supersession refs.

## TemporalKGRuntimeReport

- `identity_refs`
- `projection_record_refs`
- `adjudication_record_refs`
- `conflict_record_refs`
- `supersession_refs`
- `invalidation_refs`
- `source_verified_fact_refs`
- `source_published_output_refs`
- `source_event_refs`
- `evidence_packet_refs`
- `projection_watermark_refs`
- `policy_decision_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `contract_only_refs`
- `missing_runtime_refs`
- `failure_type`
- `failure_report_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`

Validation:

- Pass reports require identity, projection, canonical source, evidence, watermark, policy, command, event cursor, outbox, and replay refs.
- Needs-review reports require contract-only or missing-runtime refs.
- Fail reports require failure type plus failure or missing refs.

## TemporalKGFixtureManifest

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `expected_failure_type`
- `negative_case`

Validation:

- Target profile is required.
- Negative fixtures cannot expect pass.
- Expected failure type requires `negative_case = true`.
