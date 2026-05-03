# Implementation Plan: VeraCrawl Target Crawl Runtime

**Branch**: `034-target-crawl-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/034-target-crawl-runtime/spec.md`

## Summary

Implement an executable target crawl runtime that accepts a crawl objective, drives a policy-gated frontier across multiple website patterns, uses framework-neutral AI recommendations for planning and repair, produces evidence-backed outputs, graph/export/replay closure, and validates success/negative fixtures through a new CLI. The implementation will add a cohesive `target_runtime` slice while reusing existing contracts and gates from specs 001-033.

## Technical Context

**Language/Version**: Python 3.11+ project; validation uses Python 3.12 in CI/local gates
**Primary Dependencies**: Existing `pydantic` contracts and Python standard library only for core runtime; no concrete agent framework, model SDK, storage client, queue client, browser runtime, HTTP client, UI framework, or site scraper dependency in core
**Storage**: In-memory deterministic runtime records and local fixture output files for this feature; production stores remain behind existing ports/adapters
**Testing**: `pytest`, `ruff`, `mypy`, `veracrawl-contracts validate`, CLI fixture loops, full non-Docker suite, Docker-backed suite
**Target Platform**: Python library and CLI runtime on developer/server environments
**Project Type**: Single Python package with executable CLI entry point
**Performance Goals**: Complete deterministic target runtime fixture loop within 60 seconds; avoid network instability in acceptance fixtures
**Constraints**: General-purpose AI agent crawler only; low coupling/high cohesion; framework-neutral agents; command/event/replay/evidence before completion; no unsafe access or deceptive readiness claims
**Scale/Scope**: One target runtime product path with success, needs-review, repair, policy-denied, replay-mismatch, prompt-injection, missing-evidence, partial-export, and false-complete fixtures; multi-pattern success must cover at least seven website patterns in one run
**VeraCrawl Owner Services**: control, scheduler, fetch, normalize, extract, evidence, verify, publish, graph, agents, review_replay, export, ops, policy, artifact_lifecycle, tests
**Canonical Contracts**: Existing `CrawlObjective`, `CrawlPlan`, `CrawlRun`, `FrontierItem`, `SourceAdapterResult`, `AgentRecommendation`, `EvidencePacket`, `VerificationDecision`, `PublishedOutput`, `OutputManifest`, `ReplayBundleManifest`, plus new target runtime report/fixture/record contracts
**Replay/Artifact Impact**: Runtime reports must reference command results, events, event cursors, outbox records, source observations, artifact refs, output manifests, graph refs, export receipts, AI traces, policy decisions, replay bundles, and oracle results
**Security/Policy Impact**: Evaluate source scope, robots/terms, credential, browser approval, prompt-injection taint, AI tool calls, publication, export, retention, privacy lifecycle, and replay exposure before success

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

### Documentation (this feature)

```text
specs/034-target-crawl-runtime/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── target-crawl-runtime.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/veracrawl/
├── cli/
│   └── target_runtime.py
├── contracts/
│   ├── __init__.py
│   ├── enums.py
│   ├── registry.py
│   └── target_runtime.py
└── target_runtime/
    ├── __init__.py
    └── runner.py

tests/
├── contract/
│   └── test_target_runtime_contracts.py
├── fixtures/
│   └── target-runtime-*/
├── helpers/
│   └── target_runtime_fixture_assertions.py
├── integration/
│   └── test_target_runtime_fixtures.py
└── unit/
    ├── test_target_runtime_import_boundaries.py
    └── test_target_runtime_runner.py
```

**Structure Decision**: Add a focused `target_runtime` package rather than expanding `control.runtime`. Existing `control.runtime` remains the lower-level runtime spine; 034 composes target architecture behavior and acceptance reporting at a higher product-runtime layer. Contracts stay in `veracrawl.contracts`, CLI stays in `veracrawl.cli`, fixture assertions stay in tests.

## Phase 0: Research

Completed in [research.md](./research.md). Key decisions:

- Deterministic local fixture runtime is the acceptance harness; no live Internet dependency.
- New target runtime contracts wrap existing low-level references instead of duplicating all existing command/event/source/output schemas.
- Framework-neutral deterministic AI adapter records VeraCrawl-owned recommendation refs; concrete frameworks remain future adapters.
- Multi-pattern success is one aggregate run with per-pattern records, not isolated single-pattern demos.
- Negative fixtures are first-class acceptance cases and must fail before implementation is considered complete.

## Phase 1: Design And Contracts

Completed artifacts:

- [data-model.md](./data-model.md)
- [contracts/target-crawl-runtime.md](./contracts/target-crawl-runtime.md)
- [quickstart.md](./quickstart.md)

Post-design constitution check:

- [x] Target runtime remains general-purpose and pattern-driven; no single-site scraper module is introduced.
- [x] Core implementation uses Python, Pydantic contracts, and standard library only.
- [x] AI recommendations are VeraCrawl contracts with deterministic acceptance adapter behavior.
- [x] Runtime layer is cohesive and interacts with existing system through refs and typed reports.
- [x] Evidence, output, graph, export, command/event/outbox, artifact, privacy, and replay refs are required for pass.
- [x] Policy-denied, prompt-injection, missing-evidence, replay-mismatch, partial-export, and false-complete fixtures are planned.

## Complexity Tracking

No constitution violations. No complexity waiver required.
