# Data Model: Live Evidence And Verification Runtime

## LiveEvidenceVerificationRuntimeReport

- `id`, `fixture_id`, `run_ref`
- upstream refs: `schema_extraction_runtime_report_ref`
- candidate/source refs: `extraction_candidate_refs`,
  `normalized_document_refs`, `source_anchor_refs`
- evidence refs: `evidence_coverage_refs`, `evidence_packet_refs`,
  `evidence_anchor_refs`, `evidence_manifest_refs`
- verification refs: `verification_decision_refs`, `review_decision_refs`,
  `conflict_record_refs`, `contradiction_record_refs`, `freshness_refs`
- diagnostic refs: `graph_signal_refs`, `memory_refs`, `agent_reasoning_refs`
- runtime refs: `policy_decision_refs`, `privacy_lifecycle_refs`,
  `command_record_refs`, `event_cursor_refs`, `outbox_refs`,
  `replay_bundle_ref`
- forbidden refs: `publication_refs`
- failure refs: `failure_report_refs`, `missing_ref_fields`, `failure_type`,
  `operator_status`, `completion_result`, `diagnostics`

Passing reports require source-backed evidence refs, verification/review refs,
policy/privacy refs, command/event/outbox refs, and replay refs, and must have
no publication refs. Failed or needs-review reports require typed diagnostics.

## LiveEvidenceVerificationFixtureManifest

- `id`, `scenario`, `path`, `profile_refs`, `schema_ref`
- expected completion/status/failure fields
- `negative_case`
- `required_ref_types`
