# Research: Optimization Objective Gate

## Decision 1: Add an objective gate instead of another lower algorithm

**Decision**: Implement 097 as an aggregate objective-score and agent-decision
evidence gate layered after 080-096.

**Rationale**: Specs 081-096 already cover focused frontier scoring, DOM
understanding, extractor fallback, canonical dedupe, ranking, cost/recovery,
runtime wiring, owner-service integration, and 096 regression gating. The
remaining user requirement is proof that those pieces collectively optimize
time, accuracy, and cost.

**Alternatives considered**:

- Add another scoring algorithm to frontier scheduling. Rejected because 081
  and 089 already own frontier scoring and scheduler adoption.
- Add benchmark-only reporting. Rejected because benchmark output is not an
  owner-service contract and cannot substitute for replayable policy-backed
  release evidence.

## Decision 2: Deterministic objective formula is authoritative

**Decision**: Compute `OptimizationScore` deterministically from normalized
components and weights:

```text
0.35 * extraction_accuracy
+ 0.25 * intent_match_precision
+ 0.15 * crawl_success_rate
+ 0.10 * dedupe_quality
+ 0.10 * freshness
- 0.03 * normalized_latency
- 0.02 * normalized_cost
```

**Rationale**: The user supplied the objective. A deterministic formula makes
regression and release gating replayable without asking an LLM to judge whether
a run is "better".

**Alternatives considered**:

- LLM judge of optimization quality. Rejected because it is not deterministic
  and would increase cost for a release gate.
- Learning-to-rank or learned objective function now. Rejected for 097 because
  the repo lacks training data and the immediate need is testable release
  evidence. 097 preserves readiness by requiring feature/algorithm refs.

## Decision 3: LLM participates only behind explicit fallback boundaries

**Decision**: `AgentDecisionLoopEvidence` records LLM fallback as bounded
assistance, never as source evidence. Passing evidence requires deterministic
decision refs and validation refs.

**Rationale**: VeraCrawl should use AI for planning, semantic understanding,
repair proposals, and fallback structured extraction where useful, but release
claims must remain source-backed, policy-approved, and replayable.

**Alternatives considered**:

- Require LLM trace for every gate. Rejected because deterministic cases should
  avoid unnecessary cost.
- Allow LLM outputs as evidence when confidence is high. Rejected because this
  violates source-backed publication and replay principles.

## Decision 4: Release gate pass scope is the supplied validation corpus

**Decision**: `OptimizationObjectiveReleaseGate` passes only for the supplied
objective reports, agent decision loop evidence, and lower 096 regression gates.

**Rationale**: Deterministic fixture gates prove mechanics. Live or ecommerce
claims require relevant validated live/authorized/browser/deep-crawl lower
reports.

**Alternatives considered**:

- A global crawler-quality pass flag. Rejected as too broad and prone to false
  readiness.
- A deterministic-fixture-only production claim. Rejected because AGENTS.md
  requires live/authorized/browser/deep-crawl lower reports for broader claims.

## Decision 5: No new concrete adapters

**Decision**: 097 adds contracts, deterministic runtime helpers, replay helpers,
registry entries, and tests only.

**Rationale**: The gate must be reusable by any future storage, queue, model, or
browser adapter. Core packages must remain framework-neutral and low-coupled.

## Verification Plan

- Contract tests for pass/fail validation on all three new contracts.
- Unit tests for score formula, threshold behavior, agent evidence failures,
  and release gate aggregation.
- Replay tests for policy/command/event/outbox/artifact/replay refs.
- Registry tests for contracts, commands, events, fixtures, and target-area
  coverage.
- Import-boundary tests to block benchmark, adapter, browser, storage, queue,
  model SDK, or agent framework imports.
- Roadmap doc checks through review and targeted assertions where practical.
