# Implementation Plan: VeraCrawl Target Architecture Foundation

**Branch**: `001-target-architecture-foundation` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-target-architecture-foundation/spec.md`

## Summary

Build the Python foundation for VeraCrawl target architecture without turning it into a single-site scraper or coupling core to any agent framework. This plan establishes the executable project skeleton, domain contracts, ports/adapters boundaries, command/event/replay substrate, policy gates, fixture/oracle test foundations, and framework-neutral agent abstraction layer required by `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, and `.specify/memory/constitution.md`.

The first implementation phase does not claim full crawler runtime capability. It creates the contract and test foundation that later crawler, browser, source adapter, graph, memory, export, and operations implementations must satisfy. Initial executable conformance coverage targets OpenAI Agent SDK and LangGraph adapter fixtures through a generic VeraCrawl adapter contract; other named frameworks must use the same contract and remain outside core.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Pydantic v2 for contract models and JSON Schema export; standard-library `typing.Protocol` for ports; pytest for tests; ruff for lint/import boundary checks; mypy for static type checks. No agent framework is a core dependency.  
**Storage**: In-memory repositories and JSON/YAML fixture files for foundation tests. Production storage ports are defined but concrete Postgres/object store/queue adapters are not implemented in this feature.  
**Testing**: pytest unit and contract tests, adapter conformance fixtures, fixture/oracle validation checks, replay completeness checks, dependency/import boundary checks.  
**Target Platform**: Python package and CLI tooling runnable on local developer machines and CI; production deployment platforms remain adapter-defined later.  
**Project Type**: Python library plus developer CLI for contract registry validation and deterministic fixture/oracle checks.  
**Performance Goals**: Foundation contract and import-boundary tests complete in under 30 seconds on a local developer machine; registry validation is deterministic and produces stable JSON output.  
**Constraints**: Core packages must not import concrete adapters, model SDKs, browser libraries, storage clients, queue clients, or agent frameworks. Every mutating foundation path must flow through commands, owner services, policy decisions, typed results, and events. Non-fetch source adapters must not fake `FetchResult` or `PageSnapshot`.  
**Scale/Scope**: Foundation subset materializes CommandEnvelope, CommandResult, CrawlRunEvent, SourceAdapterResult, PolicyDecision, AgentRuntime/Tool/Context/Model trace contracts, ReplayBundleManifest, fixture/oracle contracts, ownership registry, source adapter interfaces, agent framework adapter conformance fixtures, and a target contract area coverage matrix for broader `docs/07` areas. Full crawler runtime, production infrastructure adapters, browser execution, graph/memory engines, and export connectors are sequenced to later specs.
**VeraCrawl Owner Services**: `control`, `fetch`, `browser`, `normalize`, `artifact_lifecycle`, `agents`, `runtime_events`, `policy`, `ports`, `review_replay`, and `ops` are directly affected. `scheduler`, `extract`, `evidence`, `verify`, `publish`, `projection`, `graph`, `memory`, and `export` receive skeleton package boundaries and registry placeholders only.  
**Canonical Contracts**: CommandEnvelope, CommandResult, CommandTypeSpec, BaseCommandPayload, SourceAdapterSpec, SourceAdapterResult, PolicyDecision, CrawlRunEvent, EventTypeSpec, AgentRuntimeSpec, AgentToolSpec, ContextRef, ContextBundle, AgentRunRequest, AgentRunResult, ModelRequest, ModelResponse, AgentActionTrace, ModelCallTrace, ToolCallTrace, ContextBundleTrace, ReplayBundleManifest, BenchmarkFixtureManifest, ExpectedOutputOracle, ExpectedEvidenceCoverageOracle, ExpectedEventSequenceOracle, ExpectedGraphOracle, FailureInjectionPlan, DRRestoreOracle, ReplayBundleOracle, TargetContractAreaCoverage.  
**Replay/Artifact Impact**: Foundation replay validation requires event cursor refs, artifact hash refs, source adapter result refs, command result refs, agent/model/tool/context trace refs, policy decision refs, deterministic clock ref, randomness seed ref, redaction map ref, and explicit missing-ref behavior.  
**Security/Policy Impact**: Source scope, robots/terms/customer authorization, credential/session use, prompt context taint/redaction, browser interaction side effects, export/withdrawal, memory retrieval, graph signal use, artifact lifecycle, retention, and recovery policy gates must have typed denial behavior and negative tests.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

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
specs/001-target-architecture-foundation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── agent-framework-adapter.md
│   ├── fixture-oracle.md
│   ├── foundation-contract-registry.md
│   └── source-adapter.md
└── tasks.md              # Created by $speckit-tasks, not by $speckit-plan
```

### Source Code (repository root)

```text
pyproject.toml
src/
└── veracrawl/
    ├── __init__.py
    ├── cli/
    │   ├── __init__.py
    │   ├── contracts.py
    │   └── fixtures.py
    ├── contracts/
    │   ├── __init__.py
    │   ├── agent.py
    │   ├── command.py
    │   ├── event.py
    │   ├── fixture.py
    │   ├── policy.py
    │   ├── replay.py
    │   ├── source_adapter.py
    │   └── registry.py
    ├── policy/
    │   ├── __init__.py
    │   └── gates.py
    ├── runtime_events/
    │   ├── __init__.py
    │   ├── event_store.py
    │   └── replay.py
    ├── ports/
    │   ├── __init__.py
    │   ├── agent_runtime.py
    │   ├── clock.py
    │   ├── source_adapter.py
    │   └── stores.py
    ├── control/
    ├── scheduler/
    ├── fetch/
    ├── browser/
    ├── normalize/
    ├── extract/
    ├── evidence/
    ├── verify/
    ├── publish/
    ├── artifact_lifecycle/
    ├── projection/
    ├── graph/
    ├── memory/
    ├── agents/
    │   ├── __init__.py
    │   ├── runtime.py
    │   ├── tool_gateway.py
    │   └── conformance.py
    ├── review_replay/
    ├── export/
    ├── ops/
    └── adapters/
        ├── __init__.py
        ├── agent_frameworks/
        │   ├── __init__.py
        │   ├── openai_agent_sdk.py
        │   └── langgraph.py
        └── sources/
            ├── __init__.py
            ├── fetch_like_stub.py
            └── non_fetch_stub.py

tests/
├── contract/
│   ├── test_contract_registry.py
│   ├── test_command_event_replay_contracts.py
│   ├── test_agent_framework_conformance.py
│   ├── test_source_adapter_conformance.py
│   └── test_import_boundaries.py
├── fixtures/
│   ├── foundation-fetch-like/
│   ├── foundation-non-fetch/
│   ├── foundation-policy-blocked-source/
│   └── foundation-replay-missing-ref/
├── unit/
│   ├── test_policy_gates.py
│   └── test_replay_validation.py
└── integration/
    └── test_foundation_fixture_runner.py
```

**Structure Decision**: Use a single Python package with `src/` layout. Core packages depend inward on `veracrawl.contracts`, `veracrawl.policy`, `veracrawl.runtime_events`, and `veracrawl.ports`; concrete source and agent framework integrations live only under `veracrawl.adapters`. Empty domain package skeletons are allowed in this feature only when paired with import-boundary tests and ownership registry entries so later tasks cannot collapse boundaries.

## Phase 0: Research

Phase 0 decisions are captured in [research.md](research.md). All open implementation choices from the spec have been resolved without weakening the target architecture:

- Python 3.11+ and Pydantic v2 are selected for executable contracts and schema export.
- `typing.Protocol` ports define runtime, source adapter, store, clock, and gateway boundaries.
- Agent framework compatibility is implemented through VeraCrawl-owned request/result/trace contracts and conformance fixtures, not by persisting framework-native state.
- Source adapter results use a typed union with natural result semantics instead of forcing every source into fetch/page snapshot contracts.
- Replay and fixture/oracle gates are blocking acceptance checks for this foundation.

## Phase 1: Design And Contracts

Phase 1 design artifacts are:

- [data-model.md](data-model.md): entities, validation rules, ownership, relationships, and foundation state transitions.
- [contracts/foundation-contract-registry.md](contracts/foundation-contract-registry.md): registry requirements, target contract area coverage, owner mappings, event links, and required tests.
- [contracts/agent-framework-adapter.md](contracts/agent-framework-adapter.md): framework-neutral agent adapter contract and initial OpenAI Agent SDK/LangGraph conformance baseline.
- [contracts/source-adapter.md](contracts/source-adapter.md): source adapter port contract, result mapping, policy-denied behavior, and fetch-like/non-fetch fixtures.
- [contracts/fixture-oracle.md](contracts/fixture-oracle.md): deterministic output, evidence, event, graph, failure, DR restore, and replay fixture/oracle validation contract.
- [quickstart.md](quickstart.md): expected developer flow and verification commands for the implementation tasks.

## Post-Design Constitution Check

- [x] Design artifacts preserve target capability and explicitly state that this foundation is not full runtime completion.
- [x] Core package boundaries keep agent frameworks and infrastructure SDKs outside VeraCrawl core.
- [x] Command, event, replay, policy, source adapter, and agent adapter contracts have owner services and test categories.
- [x] Fixture/oracle and replay negative cases are specified before implementation.
- [x] No constitution violation or justified complexity exception is present.

## Complexity Tracking

No constitution violations are introduced. No complexity exception is required.
