# Feature Specification: Graph And Memory Production Runtime

**Feature Branch**: `051-graph-memory-production-runtime`
**Created**: 2026-05-03
**Status**: Active implementation spec
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`
**Input**: Roadmap row 051 plus user hard constraints that VeraCrawl target
architecture must be implemented honestly without weakening general-purpose AI
agent crawler capability.

## Purpose

Wire advanced graph projections and memory retrieval/write paths into live crawl
planning, frontier prioritization, extraction repair, and operator explanation
without allowing graph, temporal KG, memory, or agent reasoning to satisfy
source evidence requirements.

This spec makes the graph/memory intelligence profile executable as a production
runtime slice. It composes the already materialized live normalization,
live evidence, multi-agent repair, graph frontier/review, temporal KG, and memory
kernel contracts into a single pass/fail aggregate that can be used by later
scale, ops, and benchmark specs.

## User Stories

### US1 - Graph And Memory Guide Crawl Decisions (P1)

As the crawl runtime, I need URL, redirect, canonical, page-structure, entity,
task, and temporal graph refs plus scoped memory retrieval/write refs to
influence frontier decisions while every decision remains policy-gated,
explainable, evented, and replayable.

Acceptance:

- A passing report includes live normalization, live evidence, multi-agent,
  advanced graph, graph frontier/review, temporal KG, and memory kernel refs.
- Frontier explanations cite graph signal refs and memory retrieval traces but
  also retain source-backed evidence and verification refs.
- URL, redirect, canonical, page structure, entity, task, and temporal graph
  projection refs are present.
- Site, task, repair, and run-diary memory write/retrieval refs are present.

### US2 - Graph And Memory Help Repair Without Becoming Evidence (P1)

As a repair workflow, I need graph signals and scoped memory to explain crawl,
extraction, and drift repairs while publication remains blocked unless source
evidence, verification, policy, and replay refs are present.

Acceptance:

- Repair explanations include graph and memory signal refs, multi-agent repair
  refs, owner command refs, rollback/review refs, and replay refs.
- Graph-as-evidence and memory-as-evidence scenarios fail with typed failures.
- Stale or invalidated memory used for planning fails unless invalidation and
  exclusion refs are present.

### US3 - Operators Can Audit Graph/Memory Influence (P2)

As an operator, I need one report that shows which graph and memory inputs
influenced planning and repair, which evidence anchored publication eligibility,
and why a run passed, failed, or needs review.

Acceptance:

- Operator explanations include graph, memory, frontier, repair, evidence,
  policy, command/event/outbox, freshness, invalidation, and replay refs.
- Replay mismatch and missing explanation scenarios fail deterministically.
- The runtime remains framework-neutral and imports no graph store, vector DB,
  model SDK, browser library, queue client, storage client, or agent framework.

## Functional Requirements

- **FR-001**: The runtime MUST emit a
  `GraphMemoryProductionRuntimeReport` with live normalization, live evidence,
  multi-agent repair, graph projection, graph frontier/review, temporal KG, and
  memory kernel refs before it can pass.
- **FR-002**: The runtime MUST include URL, redirect, canonical,
  page-structure, entity, task, and temporal graph projection refs.
- **FR-003**: The runtime MUST include site, task, repair, and run-diary memory
  write refs plus retrieval trace refs, freshness refs, and invalidation refs.
- **FR-004**: The runtime MUST include graph/memory-influenced frontier
  decision refs and repair explanation refs with operator-visible explanation
  refs.
- **FR-005**: The runtime MUST include source evidence refs, verification
  decision refs, policy refs, privacy refs where applicable, command refs,
  event cursor refs, outbox refs, and replay bundle refs for pass.
- **FR-006**: The runtime MUST reject graph, temporal KG, memory, and agent
  reasoning refs as source evidence.
- **FR-007**: The runtime MUST fail stale memory use unless invalidation and
  exclusion refs prove stale memory was not used for publication eligibility.
- **FR-008**: The runtime MUST fail missing live normalization, live evidence,
  multi-agent repair, graph projection, temporal KG, memory kernel, frontier
  explanation, repair explanation, invalidation, or replay refs with typed
  `GraphMemoryProductionFailureType` diagnostics.
- **FR-009**: The runtime MUST expose a CLI fixture runner
  `veracrawl-graph-memory-runtime` that validates manifests and writes
  deterministic run reports.
- **FR-010**: The runtime MUST be deterministic, fixture/oracle testable,
  framework-neutral, and free of direct dependencies on agent frameworks, graph
  stores, vector stores, queues, storage clients, browser engines, or model SDKs.

## Edge Cases

- Missing live normalization means graph inputs are not anchored to normalized
  documents and must fail.
- Missing live evidence means graph/memory can still explain planning but cannot
  pass publication eligibility.
- Missing multi-agent repair refs means graph/memory repair influence is not
  connected to owner-service commands and must fail.
- Graph or memory refs submitted as evidence must fail even if all other refs
  are present.
- Stale memory without invalidation/exclusion refs must fail.
- Missing frontier or repair explanation refs must fail because operators cannot
  audit graph/memory influence.
- Replay mismatch must fail even when graph and memory refs look complete.

## Dependencies

- **Requires**: 045 Live Normalization And Site Understanding, 047 Live Evidence
  And Verification Runtime, 050 Multi-Agent Orchestration And Repair Runtime.
- **Uses existing target foundation**: 009 Advanced Graph Projection, 010 Memory
  Kernel, 028 Graph Frontier Review Runtime Gate, 029 Temporal KG Identity
  Projection Gate.
- **Blocks**: 054 Production Benchmark And Release Gate.

## Completion Gate

Graph and memory improve planning and repair while publication still requires
current or selected historical source-backed evidence, accepted verification,
policy, artifact lineage, command/event/outbox refs, and replay refs. The report
cannot pass if graph, temporal KG, memory, or agent reasoning is treated as
source evidence.

## Non-Goals

- Does not implement a single-site scraper.
- Does not make graph or memory source evidence.
- Does not allow stale memory to publish outputs.
- Does not introduce concrete graph store, vector store, queue, storage, browser,
  model SDK, or agent framework dependencies in VeraCrawl core.
