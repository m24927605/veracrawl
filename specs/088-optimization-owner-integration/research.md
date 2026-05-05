# Research: Optimization Owner-Service Integration Roadmap

## Decision 1: Use Spec 088 As Control And Cohesive Implementation Spec

**Decision**: Treat spec 088 as the roadmap/control spec for specs 089-096 and
implement the full set in one cohesive activation.

**Rationale**: The user explicitly requested all listed specs and all
implementation in one uninterrupted Spec Kit workflow. The existing governance
requires roadmap amendment before adding new production specs. A single control
spec keeps the finite set traceable while avoiding nine partially integrated
branches that would each depend on the same shared integration contracts.

**Alternatives considered**:

- Implement each spec on a separate branch: rejected for this user request
  because it would leave cross-owner contracts partially implemented between
  branches and require repeated merge coordination.
- Add integration code without roadmap amendment: rejected because it violates
  the repository Spec Kit governance.

## Decision 2: Thin Owner-Service Integration Modules

**Decision**: Add `optimization_integration.py` modules under owner packages
instead of expanding the existing runtime modules directly.

**Rationale**: Thin modules preserve cohesion: scheduler owns frontier adoption,
normalize owns DOM context adoption, extract/verify owns field adoption, graph
owns identity/dedupe adoption, publish owns ranking adoption, and ops owns
cost/recovery/release aggregation. Existing runtime code stays stable and the
integration layer remains easy to test.

**Alternatives considered**:

- Put every integration function into `veracrawl.optimization.runtime`: rejected
  because it would blur owner-service boundaries.
- Modify worker internals directly: rejected because scheduler/worker state
  should remain behind typed owner APIs and ports.

## Decision 3: Contracts Are Integration Records, Not Durable Stores

**Decision**: Add Pydantic integration contracts that carry refs to lower
runtime decisions, owner-service refs, policy refs, command/event/outbox refs,
and replay refs.

**Rationale**: The current task is activation of optimization decisions through
owner boundaries, not new persistence. Contracts make the adoption decision
replayable without forcing adapter or database changes.

**Alternatives considered**:

- Add persistence models now: rejected because concrete stores must remain
  adapter-owned and are not required to prove owner-service integration.
- Reuse arbitrary string refs without typed records: rejected because release
  gates must fail missing lower evidence and false-ready cases.

## Decision 4: Deterministic Negative Gates First

**Decision**: Negative cases for LLM-as-evidence, missing replay, stale cache,
budget overrun, unsafe recovery, duplicate variant collapse, ranking
regression, and missing lower refs are first-class tests.

**Rationale**: Optimization improves quality only if it cannot silently bypass
evidence, policy, owner-service, and replay gates.

**Alternatives considered**:

- Validate only success fixtures: rejected because most crawler regressions
  occur in blocked, stale, drifted, and partial-evidence paths.
