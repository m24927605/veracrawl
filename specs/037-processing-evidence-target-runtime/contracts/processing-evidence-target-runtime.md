# Contract: Processing/Evidence Target Runtime Gate

## Contracts

- `TargetProcessingEvidenceEntry`
- `TargetProcessingEvidenceManifest`
- `TargetProcessingEvidenceRecord`
- `TargetRuntimeFixtureManifest.processing_evidence_ref`
- `TargetRuntimeFixtureManifest.expected_processing_evidence_count`
- `TargetRuntimeReport.normalized_document_refs`
- `TargetRuntimeReport.extraction_candidate_refs`
- `TargetRuntimeReport.evidence_packet_refs`
- `TargetRuntimeReport.evidence_anchor_refs`
- `TargetRuntimeReport.publication_report_refs`

## Commands And Events

- `record_target_processing_evidence_manifest`
- `record_target_processing_evidence`
- `target_processing_evidence_manifest_recorded`
- `target_processing_evidence_recorded`

## Fixtures

- `processing-evidence-target-success`
- `processing-evidence-target-missing-normalization`
- `processing-evidence-target-missing-candidate-anchor`
- `processing-evidence-target-missing-evidence-packet`
- `processing-evidence-target-graph-only-evidence`
- `processing-evidence-target-publication-bypass`
