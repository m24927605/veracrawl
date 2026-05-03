# Research: VeraCrawl Target Product Acceptance Gate

## Decision: Product readiness is an aggregate gate over buyer-value workflows

**Rationale**: `docs/11-target-testing-and-acceptance.md` states that technical acceptance does not equal product readiness. A dedicated aggregate gate prevents individual technical slices from being falsely labeled target-ready.

**Rejected alternative**: Treat the prior source, output, website pattern, graph, memory, export, and ops gates as product readiness by implication. Rejected because none of those gates proves all buyer-value workflows and minimum product gates together.

## Decision: Product acceptance remains deterministic and backend-neutral

**Rationale**: The current Spec Kit slices use deterministic fixture/oracle gates to prevent false claims without coupling core to external runtimes. Product acceptance should reuse stable refs from those slices and leave live UI/runtime concerns to their owner adapters.

**Rejected alternative**: Drive a real browser UI workflow. Rejected because this feature is a readiness contract and fixture gate, not a frontend implementation, and UI automation would introduce unrelated framework coupling.

## Decision: Status accuracy is a first-class failure mode

**Rationale**: `docs/09` forbids using `complete` unless the capability is both verified and operational, and `docs/11` requires zero instances where planned, scaffolded, failed, or degraded capability is labeled complete, verified, or operational.

**Rejected alternative**: Store status accuracy as free-form report text. Rejected because deterministic negative fixtures need typed failure contracts.

## Decision: Needs-review is reserved for missing live product runtime refs

**Rationale**: Some readiness evidence may rely on live runtime signals. Missing live refs must not pass, but should be distinguishable from typed defects in deterministic fixtures.

**Rejected alternative**: Fail every missing runtime case. Rejected because previous operational gates use `needs_review` to avoid false pass while preserving operator triage.
