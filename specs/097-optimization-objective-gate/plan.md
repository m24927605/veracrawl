# Implementation Plan: Optimization Objective Gate

**Branch**: `097-optimization-objective-gate-attempt` | **Date**: 2026-05-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/097-optimization-objective-gate/spec.md`

## Summary

Add the missing end-to-end optimization proof layer after specs 080-096. The
implementation introduces three adapter-free, replayable contracts:
`OptimizationObjectiveScore`, `AgentDecisionLoopEvidence`, and
`OptimizationObjectiveReleaseGate`. Runtime helpers compute the approved
weighted objective formula, validate agent observe/think/act/verify decision
loops, and aggregate lower spec 096 regression gate evidence into a final
optimization claim for a recorded corpus.

The feature keeps lower algorithms in their existing owner modules. 097 does
not reimplement frontier scoring, DOM understanding, extraction fallback,
dedupe, ranking, cost/cache, or drift recovery. It verifies that those lower
reports collectively prove "faster, more accurate, cheaper" through typed
metrics, policy refs, command/event/outbox refs, replay bundles, and negative
fixtures.

## Technical Context

**Language/Version**: Python 3.x
**Primary Dependencies**: Existing VeraCrawl Pydantic contracts, optimization
runtime services, ops integration reports, review replay helpers, pytest, ruff,
mypy
**Storage**: No new persistence adapter; deterministic refs and existing port
boundaries only
**Testing**: pytest contract, unit, replay, registry, import-boundary, and full
regression suite
**Target Platform**: VeraCrawl Python crawler runtime and ops/replay packages
**Project Type**: Python package with Spec Kit artifacts and deterministic tests
**Performance Goals**: Objective-score computation is deterministic and O(1)
per report. Gate aggregation is O(n) over supplied lower reports. No LLM, HTTP,
browser, storage, queue, or benchmark runtime is invoked by the gate.
**Constraints**: General-purpose crawler only; Python; framework-neutral;
adapter-free core; source-backed lower evidence; no unsafe source access; no
benchmark imports in core optimization objective modules
**Scale/Scope**: Aggregates 080-096 optimization evidence for recorded
validation corpora and future live/authorized/browser/deep-crawl lower reports
**VeraCrawl Owner Services**: ops and review_replay own objective gating and
replay validation; scheduler, normalize, extract/verify, graph, publish, and
cost/recovery services supply lower refs
**Canonical Contracts**: `OptimizationObjectiveScore`,
`AgentDecisionLoopEvidence`, `OptimizationObjectiveReleaseGate`,
`OptimizationRegressionReleaseGate`, `OptimizationMetricSlice`,
`AlgorithmRecommendation`, command/event registry entries
**Replay/Artifact Impact**: Passing reports require policy decision refs,
command record refs, event cursor refs, outbox refs, artifact refs where
applicable, model/tool trace refs where agent fallback is used, and replay
bundle refs
**Security/Policy Impact**: Gates fail unsafe browser escalation, credential
misuse, CAPTCHA solving, login-wall bypass, WAF evasion, raw secret persistence,
prompt-injection-tainted evidence, LLM-only evidence, and missing policy refs

## Constitution Check

*GATE: Passed before Phase 0 research; re-checked after Phase 1 design.*

- [x] General-purpose AI agent crawler capability is preserved; no one-off
  scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution
  amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks
  are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports,
  commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are
  defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle,
  retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions,
  fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint
  pressure, or delivery speed.

## Project Structure

### Documentation

```text
specs/097-optimization-objective-gate/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── contracts/
    └── objective-gate.md
```

### Source Code

```text
src/veracrawl/contracts/crawler_optimization.py
src/veracrawl/contracts/registry.py
src/veracrawl/optimization/objective_gate.py
src/veracrawl/optimization/objective_evidence.py
src/veracrawl/review_replay/crawler_optimization_objective_gate.py
src/veracrawl/cli/crawler_optimization.py
tests/contract/test_crawler_optimization_objective_gate_contracts.py
tests/contract/test_crawler_optimization_objective_gate_registry.py
tests/contract/test_crawler_optimization_objective_gate_import_boundaries.py
tests/unit/test_crawler_optimization_objective_gate.py
tests/unit/test_crawler_optimization_objective_gate_replay.py
tests/integration/test_crawler_optimization_objective_gate_cli.py
```

**Structure Decision**: Add cohesive objective-gate runtime and deterministic
evidence-runner modules under `veracrawl.optimization`, a replay validator under
`review_replay`, and a thin CLI command under `veracrawl.cli`. Shared contracts
stay in `contracts`. Core objective modules may depend on existing optimization
contracts and 096 ops integration contracts but must not import benchmarks,
adapters, browser engines, model SDKs, queue clients, storage clients, or agent
frameworks.

## Phase 0: Research

Research decisions are captured in [research.md](research.md).

## Phase 1: Design And Contracts

Data entities are captured in [data-model.md](data-model.md). Command/event and
gate contracts are captured in [contracts/objective-gate.md](contracts/objective-gate.md).
Quickstart validation is captured in [quickstart.md](quickstart.md).

## Complexity Tracking

No constitution violations are introduced by this plan.
