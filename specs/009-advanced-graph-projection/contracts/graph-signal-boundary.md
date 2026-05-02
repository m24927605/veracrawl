# Contract: Graph Signal Evidence Boundary

## Allowed

- Graph signals may influence frontier priority.
- Graph signals may influence review routing.
- Graph signals may explain drift, deduplication, or quality warnings.

## Forbidden

- Graph signals must not satisfy `source_evidence_refs`.
- Graph signals must not make publication pass without source anchors, evidence packets, verification, review, policy, and replay refs.
- Graph or memory projections must not become publication source of truth.

## Required Failure

Any graph signal offered as source evidence produces `graph_signal_as_evidence` and no pass projection or publication claim.
