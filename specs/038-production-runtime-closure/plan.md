# Implementation Plan: VeraCrawl Production Runtime Spec Roadmap

**Branch**: `038-production-runtime-closure` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/038-production-runtime-closure/spec.md`

## Summary

Define the finite post-037 production runtime spec roadmap so later work cannot
expand through ad hoc AI-generated specs. This plan creates the 038 control spec,
predeclares planned implementation specs 039-054, updates the build roadmap, and
updates agent instructions to require roadmap amendment before new production
spec creation.

## Technical Context

**Language/Version**: Documentation-only control spec; Python implementation remains unchanged.
**Primary Dependencies**: Spec Kit repository layout.
**Storage**: Markdown spec files under `specs/` and documentation under `docs/`.
**Testing**: Static validation by file presence, placeholder scan, roadmap parity, and diff checks.
**Constraints**: No runtime code implementation. Do not mark 039-054 complete.
**VeraCrawl Owner Services**: All production services are represented only as planned future work.
**Canonical Contracts**: Existing contracts remain unchanged in this control spec.
**Replay/Artifact Impact**: Future specs must preserve replay/artifact lineage; no runtime change here.
**Security/Policy Impact**: Future specs must preserve source scope, credential, browser, privacy, and export boundaries; no runtime change here.

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; the roadmap spans live acquisition, processing, evidence, agents, graph, memory, ops, scale, and release gates.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral in all planned specs.
- [x] Low coupling/high cohesion boundaries are required in every planned spec.
- [x] Evidence, verification, publication, replay, and artifact lineage are required for affected future specs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are required for affected future specs.
- [x] Future command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests must be planned when each spec activates.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Structure

```text
specs/038-production-runtime-closure/
├── spec.md
├── plan.md
├── tasks.md
└── checklists/requirements.md

specs/039-production-run-control-api/spec.md
...
specs/054-production-benchmark-release-gate/spec.md

docs/08-build-roadmap.md
AGENTS.md
.specify/feature.json
```

## Non-Implementation Boundary

This plan is complete when the roadmap and planned spec files exist and validate.
It intentionally does not create `tasks.md` for specs 039-054 because those specs
are planned, not activated or implemented.
