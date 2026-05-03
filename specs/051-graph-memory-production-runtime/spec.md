# Feature Specification: Graph And Memory Production Runtime

**Feature Branch**: `051-graph-memory-production-runtime`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Wire advanced graph projections and memory retrieval/write paths into live crawl
planning, frontier prioritization, extraction repair, and operator explanation
without treating graph or memory as source evidence.

## Scope

- URL, redirect, canonical, page structure, entity, task, and temporal graph
  projection from live artifacts and verified outputs.
- Memory retrieval/write refs for site, task, repair, and run diary contexts.
- Graph/memory-influenced frontier and repair explanations.
- Freshness, invalidation, and replay refs.

## Dependencies

- Blocks: 054.
- Requires: 045, 047, 050.

## Completion Gate

Graph and memory improve planning and repair while publication still requires
current or selected historical source-backed evidence, verification, policy, and
replay refs.

## Non-Goals

- Does not use graph or memory as source evidence.
- Does not allow stale memory to publish outputs.
