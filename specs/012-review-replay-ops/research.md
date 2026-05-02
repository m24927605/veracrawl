# Research: VeraCrawl Review Replay Ops Console

## Decision: Build A Contract/Runtime Spine Before UI

- **Rationale**: Target docs require review queue, replay console, quality dashboard, failure records, recovery actions, and operator visibility. The safest next dependency is the replayable data surface and fixture proof, not a UI shell.
- **Rejected alternative**: Build a frontend dashboard first. Rejected because a UI without replay-critical contracts could falsely imply operational readiness.

## Decision: Keep Ops Console Deterministic

- **Rationale**: Existing target slices use deterministic fixtures to prove contracts, boundaries, negative cases, and replay refs before production adapters are added.
- **Rejected alternative**: Introduce metrics, tracing, queue, or storage dependencies now. Rejected because those are later adapter/scale concerns and would couple the core prematurely.

## Decision: Treat Unsafe Recovery As A Policy Failure

- **Rationale**: Recovery actions can delete artifacts, withdraw outputs, rebuild projections, scale workers, or restore backups. Those actions must be policy/review gated and replay-visible.
- **Rejected alternative**: Allow recovery records without approvals and rely on operator discipline. Rejected because it creates hidden mutable side effects.

## Decision: Register Review/Replay/Ops As Target Materialized Contracts

- **Rationale**: `docs/07-data-contracts.md` already defines `ReviewItem`, `FailureRecord`, `RecoveryAction`, `DRRestoreReport`, and `QualityReport`. The registry must stop treating ops as only a placeholder once executable contracts and tests exist.
- **Rejected alternative**: Leave ops in placeholder status. Rejected because this feature materializes a real executable target slice.
