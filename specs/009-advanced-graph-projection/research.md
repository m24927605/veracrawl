# Research: VeraCrawl Advanced Graph Projection Spine

## Decisions

### Decision 1: Projection Is Derived State, Not Source Of Truth

Projection specs, rebuild jobs, watermarks, deltas, quality reports, and graph signals are derived from canonical events, basic graph manifests, source evidence refs, and verified output refs. They cannot replace source evidence or publication records.

**Rationale**: This preserves replay, auditability, and the constitution boundary that graph/memory cannot become publication source of truth.

### Decision 2: Deterministic Fixture Runtime Before Production Graph Store

This slice uses stable refs and deterministic hash checks instead of a production graph store.

**Rationale**: It proves contracts, replay semantics, failure modes, and adapter boundaries before introducing storage complexity.

### Decision 3: Graph Signals Are Contracts, Not Scheduler Behavior

Graph signals include frontier/review subject refs, scores, source graph refs, explanations, and policy refs, but no concrete frontier mutation is implemented here.

**Rationale**: This keeps graph projection cohesive and lets scheduler/frontier consume signals through later command/event contracts.

### Decision 4: Temporal Graph Foundation Requires Evidence And Watermarks

Temporal graph records require source output refs, evidence packet refs, valid-time refs, entity identity refs, and projection watermark refs.

**Rationale**: Temporal graph intelligence must be explainable, rebuildable, and invalidatable from canonical state.

## Alternatives Considered

- **Direct graph store integration now**: Rejected because core must not couple to a graph store; graph store adapters belong behind later ports.
- **Using graph signals as evidence**: Rejected because it violates publication and evidence boundaries.
- **Adding framework-specific graph agents**: Rejected because core must stay agent-framework-neutral.
