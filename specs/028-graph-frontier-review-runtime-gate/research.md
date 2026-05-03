# Research: VeraCrawl Graph-Driven Frontier And Review Runtime Gate

## Decision 1: Graph Signals Influence Decisions, Not Evidence

Graph signals are consumed by decision records that carry policy, command, event, outbox, explanation, and replay refs.

**Rationale**: This preserves graph intelligence as a planning/review aid while keeping source evidence, verification, and publication authoritative.

## Decision 2: Frontier And Review Decisions Are Separate Records

Frontier decisions and review route decisions have different owners, required refs, and failure modes.

**Rationale**: Scheduler-owned priority/retry/retire/expand decisions should not blur with review queue routing. Separate records keep cohesion and validation clear.

## Decision 3: Needs Review For Missing Runtime

Contract-only graph signal descriptors are not enough to claim operational runtime pass.

**Rationale**: The target architecture requires honest runtime readiness. Missing graph/scheduler/review runtime refs must be operator-visible `needs_review`.

## Decision 4: Deterministic Fixture Runtime Before Production Graph Store

Fixtures prove runtime shape using stable contracts and refs without production graph-store or queue dependencies.

**Rationale**: Core must remain dependency-neutral. Concrete graph stores, queues, and review UI can be introduced later through adapters without changing contracts.
