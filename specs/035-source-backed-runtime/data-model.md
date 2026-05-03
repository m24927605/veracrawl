# Data Model: VeraCrawl Source-Backed Target Runtime

## TargetSourceCorpusManifest

Fields:

- `id`
- `fixture_id`
- `entry_refs`
- `expected_pattern_count`
- `policy_decision_refs`
- `replay_oracle_ref`

Validation:

- Passing corpus manifests require at least seven entries.
- Entries must be unique.

## TargetSourceCorpusEntry

Fields:

- `id`
- `website_pattern`
- `source_path`
- `content_type`
- `expected_fields`
- `evidence_markers`
- `policy_decision_ref`
- `allowed`
- `contains_prompt_injection`
- `requires_export_ref`
- `replay_hash_ref`
- `drift_aliases`

Validation:

- Allowed entries require source path, expected fields, evidence markers, and policy decision ref.
- Denied entries can be used only in blocked fixtures.
- Prompt-injection entries cannot pass.

## TargetSourceObservationRecord

Fields:

- `id`
- `run_ref`
- `corpus_entry_ref`
- `website_pattern`
- `source_path_ref`
- `content_hash_ref`
- `source_observation_ref`
- `artifact_ref`
- `extracted_field_refs`
- `evidence_refs`
- `graph_refs`
- `policy_decision_refs`
- `replay_refs`
- `missing_field_refs`
- `prompt_injection_refs`
- `result`

Validation:

- Passing observations require content hash, artifact, extracted fields, evidence, graph, policy, and replay refs.
- Failed observations require missing field, prompt injection, or failure refs.
