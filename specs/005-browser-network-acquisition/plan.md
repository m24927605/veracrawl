# Implementation Plan: VeraCrawl Browser and Network Acquisition Runtime

**Branch**: `005-browser-network-acquisition` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-browser-network-acquisition/spec.md`

## Summary

Implement the next target architecture acquisition slice after source adapter runtime: real local HTTP acquisition through a replaceable adapter, deterministic benchmark server fixtures, browser observation contracts, sandbox policy gates, network/browser replay reports, and security negative fixtures. Core packages stay coupled only to contracts and ports; concrete networking and future browser engines remain adapter-owned.

## Technical Context

**Language/Version**: Python 3.11+; local validation uses Python 3.12.  
**Primary Dependencies**: Existing dependencies only: Pydantic v2, pytest, ruff, mypy, and Python standard-library networking for the concrete local HTTP adapter. No Playwright or third-party HTTP client in core.  
**Storage**: Existing deterministic durable fixture store and artifact refs behind ports. Production storage remains out of scope.  
**Testing**: pytest contract, unit, integration, replay, fixture/oracle, negative, security/import-boundary, registry, and CLI validation.  
**Target Platform**: Python package and deterministic local CLI/test harness.  
**Project Type**: Python library plus deterministic fixture runner.  
**Performance Goals**: Full local network/browser acquisition gate completes within 30 seconds; success fixtures report zero missing network/browser replay refs.  
**Constraints**: Core must not import Playwright, concrete HTTP client packages, browser engines, storage clients, queue clients, model SDKs, agent frameworks, or site-specific scraper modules. Network execution requires policy refs, source scope, egress/private-network decisions, budgets, durable command/event/outbox refs, and artifact refs.  
**Scale/Scope**: Local deterministic HTTP static/redirect acquisition, browser read-only observation contracts/fixtures, and negative fixtures for robots, private network, egress, rate, size, redirect, timeout, and unsafe browser side effect. Production browser execution, authenticated sessions, distributed crawling, graph/memory/export, and production scale are not implemented.  
**VeraCrawl Owner Services**: `fetch`, `browser`, `scheduler`, `runtime_events`, `artifact_lifecycle`, `review_replay`, `policy`, `ports`, `contracts`, and `ops` are directly affected.  
**Canonical Contracts**: NetworkRequest, NetworkResponse, RedirectHop, NetworkAcquisitionReport, BrowserSandboxPolicy, BrowserInteractionStep, SourceAdapterCommand, SourceAdapterResult, FetchAttempt, FetchResult, PageSnapshot, SourceAcquisitionReport, DurableCommandRecord, OutboxRecord, EventCursorRecord, FrontierItem, QueueLease, DurableReplayRecoveryReport.  
**Replay/Artifact Impact**: Network/browser replay requires request refs, response refs, redirect refs, raw HTML refs, DOM refs, screenshot refs, network metadata refs, source adapter result refs, source acquisition refs, command records, event cursors, outbox refs, policy refs, frontier item refs, lease refs, and recovery report refs.  
**Security/Policy Impact**: Egress allowlist, private-network deny, robots, rate, redirect, response-size, timeout, browser side-effect, sandbox, artifact privacy lifecycle, and retention gates must be typed and operator-visible.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-check after Phase 1 design.*

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
specs/005-browser-network-acquisition/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── network-acquisition.md
│   ├── browser-observation.md
│   ├── safety-policy.md
│   └── fixture-oracle.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── veracrawl/
    ├── contracts/
    │   ├── network.py          # NetworkRequest, NetworkResponse, RedirectHop, NetworkAcquisitionReport
    │   ├── browser.py          # BrowserSandboxPolicy, BrowserInteractionStep
    │   └── registry.py
    ├── ports/
    │   ├── network.py          # NetworkClientPort
    │   └── browser.py          # BrowserObservationPort
    ├── fetch/
    │   └── network_acquisition.py
    ├── browser/
    │   └── observation.py
    ├── adapters/
    │   ├── network/
    │   │   └── stdlib_http.py
    │   └── browser/
    │       └── deterministic.py
    ├── review_replay/
    │   └── network_browser.py
    └── cli/
        └── network.py

tests/
├── contract/
│   ├── test_network_browser_contract_registry.py
│   ├── test_network_browser_contracts.py
│   └── test_network_browser_import_boundaries.py
├── unit/
│   ├── test_network_policy_gates.py
│   ├── test_browser_sandbox_gates.py
│   └── test_network_browser_replay.py
├── integration/
│   ├── test_network_acquisition_runtime.py
│   └── test_network_browser_negative_fixtures.py
├── helpers/
│   ├── benchmark_server.py
│   └── network_fixture_assertions.py
└── fixtures/
    ├── network-http-success/
    ├── network-http-redirect/
    ├── network-browser-readonly/
    ├── network-robots-blocked/
    ├── network-private-denied/
    ├── network-egress-denied/
    ├── network-rate-budget/
    ├── network-size-budget/
    ├── network-redirect-denied/
    ├── network-timeout/
    └── network-browser-unsafe-side-effect/
```

**Structure Decision**: Extend the existing single Python package. Core policy/replay orchestration lives in `fetch/network_acquisition.py` and `browser/observation.py`; concrete standard-library HTTP and deterministic browser adapters live under `adapters/`; replay validation lives under `review_replay`. Future Playwright/browser-engine adapters must implement `BrowserObservationPort` without changing core contracts.

## Phase 0: Research

Phase 0 decisions are captured in [research.md](research.md). The core choices are:

- Use Python standard-library HTTP in a concrete adapter for real local network testing without adding a third-party client dependency.
- Use deterministic benchmark server fixtures as the only network target in automated tests.
- Keep browser execution framework-neutral by implementing contracts, sandbox gates, and deterministic read-only observation fixtures before any Playwright adapter.
- Treat egress, private network, robots, rate, size, redirect, timeout, and unsafe browser side effects as typed non-success outcomes.

## Phase 1: Design And Contracts

Phase 1 design artifacts are:

- [data-model.md](data-model.md): network/browser acquisition entities, validation rules, and transitions.
- [contracts/network-acquisition.md](contracts/network-acquisition.md): request, response, redirect, network acquisition, raw artifact behavior.
- [contracts/browser-observation.md](contracts/browser-observation.md): browser sandbox policy, browser interaction step, DOM/screenshot/network artifact refs.
- [contracts/safety-policy.md](contracts/safety-policy.md): egress, private network, robots, rate, size, timeout, redirect, and side-effect gates.
- [contracts/fixture-oracle.md](contracts/fixture-oracle.md): success and negative fixture/oracle requirements.
- [quickstart.md](quickstart.md): expected validation flow.

## Post-Design Constitution Check

- [x] Network/browser acquisition is general and fixture-driven, not a single-site scraper.
- [x] Core depends only on contracts, ports, commands, events, policy, scheduler refs, artifact refs, and replay.
- [x] Network and browser policy failure gates are blocking.
- [x] Negative fixture/oracle coverage is defined before implementation.
- [x] No constitution violation or justified complexity exception is present.

## Complexity Tracking

No constitution violations are introduced. No complexity exception is required.
