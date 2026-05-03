# Implementation Plan: Production Run Control API

**Branch**: `039-production-run-control-api` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/039-production-run-control-api/spec.md`

## Summary

Add a production run-control slice that creates project/site/objective/plan/run
control records, enforces approval, budget, policy snapshot, lifecycle, and
replay gates, and exposes deterministic CLI fixtures for success and negative
paths. This is the control-plane prerequisite for specs 040, 041, 044, 049, and
054; it intentionally does not implement live source acquisition.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12
**Primary Dependencies**: Pydantic; pytest/ruff/mypy for validation
**Storage**: Deterministic in-memory repositories and fixture run reports
**Testing**: Contract, unit, integration fixture tests, registry validation, CLI loop
**Target Platform**: Python package and CLI
**Project Type**: Library/CLI
**Performance Goals**: Deterministic fixture execution; no production SLO in this spec
**Constraints**: No concrete persistence, browser, source acquisition, model, or agent framework coupling
**Scale/Scope**: Control-plane lifecycle for one run per fixture
**VeraCrawl Owner Services**: control, policy, runtime_events, review_replay, tests
**Canonical Contracts**: CrawlObjective, CrawlPlan, CrawlRun, CommandResult, CrawlRunEvent, PolicyDecision, ReplayBundleManifest plus new run-control contracts
**Replay/Artifact Impact**: Lifecycle records require command/event/replay refs
**Security/Policy Impact**: Runs require source/publication policy refs, approval refs, budget refs, and policy snapshot refs

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; run control is source/domain agnostic.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral; no agent framework is introduced.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, CLI, and control runtime module.
- [x] Evidence, verification, publication, replay, and artifact lineage are preserved as downstream gates.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export gates remain blocking downstream requirements.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Structure

```text
specs/039-production-run-control-api/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/production-run-control-api.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/objective.py
src/veracrawl/control/run_control.py
src/veracrawl/cli/run_control.py
tests/fixtures/production-run-control-*/
```

## Implementation Notes

- Add contracts to `contracts/objective.py` because they extend objective/run
  control ownership and avoid a new disconnected domain module.
- Keep execution deterministic and local. Production persistence wiring is spec
  040.
- Register commands/events for lifecycle operations so later specs can reuse the
  taxonomy.
