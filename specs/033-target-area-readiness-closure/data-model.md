# Data Model: Target Area Readiness Impact Closure

## TargetContractAreaCoverageRegistration

Existing fields used:

- `coverage_status`
- `materialized_contract_refs`
- `placeholder_contract_refs`
- `followup_spec_gate`
- `replay_impact`
- `privacy_lifecycle_impact`

Validation rule:

- `coverage_status == materialized` requires non-empty materialized refs, no placeholders, no follow-up gate, and impact text without unresolved target-complete prerequisite wording.
- non-materialized status continues to require `followup_spec_gate`.
