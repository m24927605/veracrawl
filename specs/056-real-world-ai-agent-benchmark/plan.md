# Implementation Plan: Real-World AI Agent Crawl Planning And Extraction Benchmark

**Branch**: `056-real-world-ai-agent-benchmark` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/056-real-world-ai-agent-benchmark/spec.md`

## Summary

Build a row 056 benchmark that composes row 055 live public corpus acquisition with VeraCrawl's framework-neutral model and agent runtime ports. The runtime will execute four AI-mediated decision phases per public site, persist canonical trace contracts, create source-anchored extraction candidates, reject LLM-as-evidence and publication bypass, expose a CLI, register contracts/commands/events/fixture oracles, and validate with focused tests plus a live public run.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Existing `pydantic`; no new runtime dependency  
**Storage**: Existing reference persistence store for live corpus state; JSON outputs for benchmark artifacts  
**Testing**: pytest, ruff, mypy, registry validation, Docker-backed pytest  
**Target Platform**: Python library/CLI  
**Project Type**: Single Python package  
**Performance Goals**: One read-only target fetch plus one robots preflight per row 055 site; four model/agent decisions per passing site  
**Constraints**: General-purpose AI crawler; low coupling/high cohesion; no single-site scraper; core must not import concrete model SDKs, agent frameworks, HTTP adapters, browser runtimes, storage clients, or framework-native state  
**Scale/Scope**: Public corpus benchmark gate for at least four public targets, with deterministic fixture tests and one live validation run  
**VeraCrawl Owner Services**: `ops`, `agents`, `fetch`, `evidence`, `verify`, `publish`, `review_replay`, `tests`  
**Canonical Contracts**: `RealWorldAIAgentDecisionTrace`, `RealWorldAIAgentExtractionCandidate`, `RealWorldAIAgentBenchmarkRunReport`, `RealWorldAIAgentBenchmarkManifest`, plus existing `ModelRequest`, `ModelResponse`, `ModelCallTrace`, `AgentRunRequest`, `AgentRunResult`, `AgentActionTrace`, `ToolCallTrace`, `ContextBundleTrace`, and `RealWorldBenchmarkRunReport`  
**Replay/Artifact Impact**: AI decisions and candidates require source anchors, artifacts, content hashes, command/event/outbox refs, and replay refs; aggregate report requires replay bundle refs and row 055 replay refs  
**Security/Policy Impact**: Reuses row 055 allowlist/robots/private-network gates; enforces prompt/context trace refs, raw prompt/response redaction, no LLM-as-evidence, no publication bypass, and no framework-native canonical state

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

### Documentation

```text
specs/056-real-world-ai-agent-benchmark/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── real-world-ai-agent-benchmark.md
└── tasks.md
```

### Source Code

```text
src/veracrawl/
├── benchmarks/
│   └── real_world_ai_agent.py
├── cli/
│   └── real_ai_benchmark.py
├── contracts/
│   ├── enums.py
│   ├── real_world_ai_agent.py
│   ├── registry.py
│   └── __init__.py
└── review_replay/
    └── real_world_ai_agent.py

tests/
├── contract/
│   ├── test_real_world_ai_agent_contracts.py
│   ├── test_real_world_ai_agent_contract_registry.py
│   └── test_real_world_ai_agent_import_boundaries.py
├── integration/
│   └── test_real_world_ai_agent_fixtures.py
├── unit/
│   ├── test_real_world_ai_agent_runtime.py
│   └── test_real_world_ai_agent_replay.py
└── fixtures/
    ├── real-world-ai-agent-public-corpus/
    ├── real-world-ai-agent-missing-model-trace/
    ├── real-world-ai-agent-candidate-missing-source-anchor/
    ├── real-world-ai-agent-llm-output-as-evidence/
    ├── real-world-ai-agent-publication-bypass/
    ├── real-world-ai-agent-framework-state-canonical/
    └── real-world-ai-agent-missing-replay/
```

**Structure Decision**: Add a cohesive `benchmarks` runtime slice and CLI composition layer. The runtime depends only on contracts, existing row 055 result contracts, and framework-neutral ports. CLI dynamically loads concrete local/native adapters.

## Complexity Tracking

No constitution violations.
