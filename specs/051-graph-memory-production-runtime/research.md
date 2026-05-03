# Research: Graph And Memory Production Runtime

## Decision 1: Add A Dedicated Integration Aggregate

Row 051 spans graph projection, graph frontier/review, temporal KG, memory
kernel, live evidence, and multi-agent repair. The implementation will add
`GraphMemoryProductionRuntimeReport` instead of overloading graph, memory, or
multi-agent reports.

Rationale:

- Existing graph and memory reports already have clear owner-service semantics.
- The production closure requirement is cross-cutting and needs one replayable
  pass/fail surface for later scale, ops, and benchmark specs.
- The aggregate can enforce dependency refs without changing lower-level gates.

Rejected alternative:

- Extend `MemoryKernelReport` or `GraphFrontierReviewRuntimeReport` with all row
  051 dependencies. That would blur owner boundaries and make graph or memory
  appear authoritative for publication eligibility.

## Decision 2: Passing Reports Require Source Evidence And Verification Refs

Graph and memory influence planning and repair, but a passing row 051 report
must include source evidence and verification refs from row 047. Graph, temporal
KG, memory, and agent reasoning refs are diagnostic/planning context only.

Rationale:

- The constitution forbids graph/memory from substituting for source evidence.
- Row 054 needs a single assertion that graph/memory was helpful without
  weakening publication gates.

Rejected alternative:

- Let graph/memory pass independently and rely on publication to catch missing
  evidence later. That would create misleading runtime readiness claims.

## Decision 3: Memory Freshness And Invalidation Are First-Class Gate Inputs

Passing reports must include memory freshness refs plus invalidation/exclusion
refs. Stale-memory scenarios fail unless they prove stale memory was excluded
and cannot influence publication eligibility.

Rationale:

- Memory reuse is useful only if freshness and invalidation are auditable.
- It prevents stale repair heuristics from silently shaping outputs.

Rejected alternative:

- Treat memory freshness as an internal implementation detail. That would make
  replay and operator audit incomplete.

## Decision 4: Runtime Remains Deterministic And Store-Agnostic

The row 051 runtime creates typed refs and composes existing deterministic gates.
It does not import graph stores, vector stores, queue clients, storage clients,
browser libraries, model SDKs, or agent frameworks.

Rationale:

- Concrete storage and scale behavior belongs to row 052 and later adapter
  specs.
- The core contract must stay framework-neutral and replayable.

Rejected alternative:

- Introduce graph/vector store clients in the runtime. That would couple core to
  infrastructure and make focused fixture tests non-deterministic.
