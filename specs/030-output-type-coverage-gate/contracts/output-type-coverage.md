# Contract: Output Type Coverage Gate

## Target Output Types

- `record`
- `table`
- `document_metadata`
- `document`
- `file`
- `dataset`
- `fact`

## Required Pass Refs

Each `OutputTypeCoverageRecord` must include:

- source evidence refs
- evidence packet and coverage refs
- verification decision refs
- published output and output manifest refs
- privacy lifecycle refs
- type-specific refs
- policy refs
- command refs
- event cursor refs
- outbox refs
- replay bundle refs

## Failure Types

- `output_type_coverage_missing_runtime_refs`
- `output_type_coverage_missing_output_type`
- `output_type_coverage_unsupported_output_type`
- `output_type_coverage_derived_context_as_evidence`
- `output_type_coverage_candidate_as_evidence`
- `output_type_coverage_graph_as_evidence`
- `output_type_coverage_memory_as_evidence`
- `output_type_coverage_agent_reasoning_as_evidence`
- `output_type_coverage_temporal_kg_as_evidence`
- `output_type_coverage_missing_table_cell_evidence`
- `output_type_coverage_missing_file_lifecycle`
- `output_type_coverage_missing_dataset_item_evidence`
- `output_type_coverage_missing_fact_verification`
- `output_type_coverage_missing_replay_refs`
