# Implementation Plan: Live HTTP Acquisition Runtime

**Branch**: `041-live-http-acquisition-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/041-live-http-acquisition-runtime/spec.md`

## Summary

Add a production live HTTP acquisition gate that composes row 039 run control,
row 040 persistence wiring, existing network/source adapter ports, and target
source observation records. The runtime uses adapter-owned standard-library HTTP
for deterministic local fixtures and keeps core packages free of concrete HTTP
client dependencies.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12
**Primary Dependencies**: Pydantic; pytest/ruff/mypy for validation
**Storage**: Row 040 reference persistence store behind ports
**Testing**: Contract, unit, integration fixture tests, registry validation, CLI loop, full gates
**Target Platform**: Python package and CLI
**Project Type**: Library/CLI
**Performance Goals**: Deterministic local HTTP fixture execution; no production throughput SLO in this spec
**Constraints**: No concrete HTTP/database/queue/object/model/agent framework coupling in core
**Scale/Scope**: One authorized HTTP source per fixture
**VeraCrawl Owner Services**: control, fetch, scheduler, runtime_events, review_replay, tests
**Canonical Contracts**: LiveHttpAcquisitionReport, LiveHttpFixtureManifest, NetworkRequest, NetworkResponse, SourceAcquisitionReport, TargetSourceObservationRecord
**Replay/Artifact Impact**: request/response, content hash, artifact, event cursor, outbox, policy, and replay refs required for pass
**Security/Policy Impact**: scope/private-network/malformed/replay/direct-bypass failures are typed

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral.
- [x] Low coupling/high cohesion boundaries are explicit through ports and contracts.
- [x] Evidence/replay/artifact lineage is defined.
- [x] Security and policy gates are defined for unsafe HTTP cases.
- [x] Fixtures and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Structure

```text
specs/041-live-http-acquisition-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/live-http-acquisition-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/enums.py
src/veracrawl/contracts/network.py
src/veracrawl/fetch/live_http.py
src/veracrawl/cli/live_http.py
tests/fixtures/live-http-*/
```

## Complexity Tracking

No constitution violations are introduced.
