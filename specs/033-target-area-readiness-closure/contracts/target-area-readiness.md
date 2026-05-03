# Contract: Target Area Readiness Impact Closure

## Registry Rules

Materialized target areas must not contain:

- `before target-complete`
- `must define`
- `placeholder`

in `replay_impact` or `privacy_lifecycle_impact`.

Materialized target areas must also have:

- no `placeholder_contract_refs`
- no `followup_spec_gate`
- non-empty `materialized_contract_refs`

Non-materialized target areas must retain explicit `followup_spec_gate` semantics.
