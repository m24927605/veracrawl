# Contract: Product Acceptance Gate

## Commands

- `record_product_workflow_readiness`
- `record_product_acceptance_gate_report`
- `record_product_acceptance_fixture_manifest`

## Events

- `product_workflow_readiness_recorded`
- `product_acceptance_gate_reported`
- `product_acceptance_fixture_manifest_recorded`

## Required Fixtures

| Fixture | Expected result |
| --- | --- |
| `product-acceptance-success` | pass |
| `product-acceptance-runtime-unavailable` | needs_review |
| `product-acceptance-missing-workflow` | fail |
| `product-acceptance-missing-minimum-gate` | fail |
| `product-acceptance-missing-evidence` | fail |
| `product-acceptance-missing-replay` | fail |
| `product-acceptance-missing-operator-visibility` | fail |
| `product-acceptance-missing-policy` | fail |
| `product-acceptance-missing-workflow-specific-refs` | fail |
| `product-acceptance-scaffold-only` | fail |
| `product-acceptance-contract-only` | fail |
| `product-acceptance-false-complete-status` | fail |
| `product-acceptance-degraded-operational` | fail |
| `product-acceptance-missing-export-reconciliation` | fail |

## Pass Requirements

- All 10 target product workflows are covered.
- All 7 minimum product gates are covered.
- Every workflow record includes evidence, replay, operator-visible result, policy, command, event cursor, outbox, artifact, acceptance oracle, workflow-specific, capability state, and status accuracy refs.
- The report includes aggregate buyer-value workflow refs and status accuracy refs.
- No planned, scaffolded, failed, degraded, or contract-only capability is labeled `complete`, `verified`, or `operational`.

## Failure Requirements

- Missing workflow, minimum gate, evidence, replay, operator visibility, policy, workflow-specific refs, or export reconciliation emits a typed failure.
- Scaffold-only, contract-only, false-complete, and degraded-operational claims emit typed failures.
- Runtime-unavailable emits `needs_review` and cannot be used to claim product readiness.
