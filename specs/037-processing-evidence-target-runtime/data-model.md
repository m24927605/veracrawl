# Data Model: VeraCrawl Processing/Evidence Target Runtime Gate

## TargetProcessingEvidenceEntry

- `id`
- `corpus_entry_ref`
- `adapter_backed_source_ref`
- `required_field_refs`
- `policy_decision_ref`
- `simulate_missing_normalization`
- `simulate_missing_candidate_anchor`
- `simulate_missing_evidence_packet`
- `simulate_graph_only_evidence`
- `simulate_publication_bypass`

## TargetProcessingEvidenceManifest

- `id`
- `fixture_id`
- `entries`
- `expected_processing_evidence_count`
- `policy_decision_refs`
- `replay_oracle_ref`

## TargetProcessingEvidenceRecord

- `id`
- `run_ref`
- `corpus_entry_ref`
- `adapter_backed_source_ref`
- `source_observation_ref`
- `adapter_output_refs`
- `normalized_document_ref`
- `extraction_candidate_ref`
- `candidate_anchor_refs`
- `evidence_packet_ref`
- `evidence_anchor_refs`
- `publication_report_ref`
- `policy_decision_refs`
- `replay_refs`
- `graph_only_evidence_refs`
- `missing_normalization_refs`
- `missing_candidate_anchor_refs`
- `missing_evidence_packet_refs`
- `publication_bypass_refs`
- `result`

Passing records require all positive refs and no diagnostic refs.
