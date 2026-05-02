# Data Model: VeraCrawl Evidence and Publication Spine

## EvidenceAnchor

- `id`
- `evidence_packet_ref`
- `candidate_ref`
- `field_name`
- `source_artifact_ref`
- `normalized_document_ref`
- `anchor_ref`
- `expected_text_hash`
- `privacy_classification`
- `policy_decision_refs`

## EvidencePacketManifest

- `id`
- `evidence_packet_ref`
- `candidate_ref`
- `coverage_result_ref`
- `evidence_anchor_refs`
- `source_artifact_refs`
- `normalized_document_refs`
- `privacy_lifecycle_refs`
- `policy_decision_refs`
- `replay_bundle_ref`
- `manifest_hash`

## ReviewDecision

- `id`
- `run_ref`
- `verification_decision_ref`
- `evidence_packet_ref`
- `decision`
- `reviewer_ref`
- `policy_decision_refs`
- `rationale_refs`

## PublicationReport

- `id`
- `run_ref`
- `candidate_ref`
- `evidence_packet_ref`
- `evidence_manifest_ref`
- `coverage_result_ref`
- `verification_decision_ref`
- `review_decision_ref`
- `publication_policy_decision_refs`
- `privacy_lifecycle_refs`
- `published_output_ref`
- `output_manifest_ref`
- `artifact_refs`
- `command_record_refs`
- `event_cursor_refs`
- `outbox_refs`
- `replay_bundle_ref`
- `failure_report_refs`
- `missing_ref_fields`
- `operator_status`
- `completion_result`

## EvidencePublicationFixtureManifest

- `id`
- `scenario`
- `profile_refs`
- `expected_completion_result`
- `expected_operator_status`
- `negative_case`
