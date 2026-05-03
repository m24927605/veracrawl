# Implementation Plan: Real Agent And Model Adapter Runtime

**Branch**: `049-real-agent-model-adapter-runtime` | **Date**: 2026-05-03 | **Spec**: `specs/049-real-agent-model-adapter-runtime/spec.md`
**Input**: Feature specification from `/specs/049-real-agent-model-adapter-runtime/spec.md`

## Summary

Implement the row 049 runtime gate that composes model provider adapters and
agent framework adapters through VeraCrawl-owned ports. The runtime must prove
planning, extraction, and repair agent turns can execute through adapter
bindings while the core persists only canonical VeraCrawl contracts, traces,
commands, events, policy, replay, and diagnostic refs. Concrete SDK/framework
imports stay in adapter/CLI composition and unavailable external SDKs must
return `needs_review` rather than a fake pass.

## Technical Context

**Language/Version**: Python 3.12 validation, package supports Python >=3.11  
**Primary Dependencies**: pydantic, existing VeraCrawl contracts/runtime helpers  
**Storage**: No concrete storage in core; deterministic refs and fixture artifacts  
**Testing**: pytest, ruff, mypy, Spec Kit prerequisite checks, Docker-backed pytest gate  
**Target Platform**: Python CLI/runtime package  
**Project Type**: single Python package  
**Performance Goals**: fixture CLI loop completes under deterministic test thresholds  
**Constraints**: general-purpose AI agent crawler, low coupling/high cohesion, framework-neutral core, no core imports of concrete model SDKs or agent frameworks  
**Scale/Scope**: target-architecture adapter runtime slice for planning/extraction/repair, not a single-site scraper or contract-only gate  
**VeraCrawl Owner Services**: agents, extract, normalize, control, review_replay, tests  
**Canonical Contracts**: AgentRunRequest, AgentRunResult, AgentActionTrace, ModelRequest, ModelResponse, ModelCallTrace, ToolCallTrace, ContextBundleTrace, ModelProviderAdapterExecutionRecord, AgentAdapterExecutionRecord, AgentModelAdapterRuntimeReport, AgentModelAdapterFixtureManifest  
**Replay/Artifact Impact**: agent/model/tool/context traces, adapter runtime refs, command/event/outbox refs, replay bundle refs, and diagnostic external SDK availability refs  
**Security/Policy Impact**: prompt redaction, raw credential exclusion, framework/provider native state exclusion, prompt injection boundary refs, policy/security/privacy refs

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; no one-off scraper assumptions are introduced.
- [x] Python remains the implementation language unless a constitution amendment changes it.
- [x] Agent runtime remains framework-neutral; model SDKs and agent frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through ports, commands, events, typed results, and owner services.
- [x] Evidence, verification, publication, replay, and artifact lineage are defined for affected outputs.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, retention, and export/withdrawal gates are defined where applicable.
- [x] Command payload schemas, event payload schemas, state transitions, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/049-real-agent-model-adapter-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/agent-model-adapter-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/{agent_model_runtime.py,enums.py,registry.py}
src/veracrawl/agents/real_adapter_runtime.py
src/veracrawl/adapters/model_providers/{local_runtime.py,external_runtime.py}
src/veracrawl/adapters/agent_frameworks/{native_runtime.py,external_runtime.py}
src/veracrawl/cli/agent_model_runtime.py
tests/contract/test_agent_model_adapter_runtime_contracts.py
tests/contract/test_agent_model_adapter_runtime_import_boundaries.py
tests/unit/test_agent_model_adapter_runtime.py
tests/unit/test_agent_model_adapter_runtime_adapters.py
tests/integration/test_agent_model_adapter_runtime_fixtures.py
tests/fixtures/agent-model-adapter-*/
```

**Structure Decision**: add a new agents aggregate for the integrated adapter
runtime and keep concrete adapter implementations in `src/veracrawl/adapters/`.
The core aggregate receives ports/bindings; it never imports adapter modules,
SDKs, framework packages, or provider clients.

## Complexity Tracking

No constitution violations.
