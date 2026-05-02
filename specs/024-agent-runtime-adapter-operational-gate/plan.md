# Implementation Plan: VeraCrawl Agent Runtime Adapter Operational Gate

**Branch**: `024-agent-runtime-adapter-operational-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/024-agent-runtime-adapter-operational-gate/spec.md`

## Summary

Implement an adapter-owned agent runtime gate that validates canonical mapping from model provider and agent framework adapters into VeraCrawl contracts. The gate remains framework-neutral in core, uses dynamic adapter loading in CLI, returns `needs_review` for missing live SDK/runtime refs, and fails unsafe or incomplete mappings.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Pydantic v2, pytest, ruff, mypy  
**Storage**: none; deterministic fixture outputs under `.veracrawl-test-runs/`  
**Testing**: contract, registry, import-boundary, unit, integration, CLI fixture loop, full pytest  
**Target Platform**: local deterministic fixture runner; future concrete SDK adapters stay optional  
**Project Type**: Python package with `src/` layout  
**Performance Goals**: deterministic fixture runs under normal unit-test latency  
**Constraints**: no core static imports of model SDKs or agent framework SDKs; no raw prompt/response persistence; no framework-native canonical state  
**Scale/Scope**: materializes adapter gate contracts, runtime, CLI, fixtures, and docs; does not call external model APIs

## Constitution Check

- [x] General-purpose crawler capability is preserved; adapters map into common contracts.
- [x] Python remains implementation language.
- [x] Agent runtime remains framework-neutral; SDKs and frameworks are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion: contracts, runtime support, adapters, CLI, and tests are separated.
- [x] No schedule-based weakening; `needs_review` is used only for missing live runtime truthfulness.
- [x] Security/privacy, prompt, credential, observability, policy, and replay refs are required.

## Project Structure

```text
specs/024-agent-runtime-adapter-operational-gate/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── agent-adapter-gate.md
│   └── boundary.md
├── checklists/
│   └── requirements.md
└── tasks.md

src/veracrawl/
├── adapters/agent_frameworks/contract.py
├── agents/adapter_gate.py
├── cli/agent_adapters.py
└── contracts/agent_adapter.py

tests/
├── contract/test_agent_runtime_adapter_contracts.py
├── contract/test_agent_runtime_adapter_contract_registry.py
├── contract/test_agent_runtime_adapter_import_boundaries.py
├── unit/test_agent_runtime_adapter_gate.py
├── helpers/agent_runtime_adapter_fixture_assertions.py
└── integration/test_agent_runtime_adapter_fixtures.py
```

## Phase Plan

1. Add specs, data model, contracts, quickstart, and tasks.
2. Add contracts/enums/registry/CLI entry point.
3. Add adapter-owned deterministic contract adapter.
4. Implement core adapter gate runtime.
5. Add fixtures, tests, and docs.
6. Run validation and record results.

## Risk Controls

- Contract-only or missing live SDK/runtime cannot pass.
- Framework-native state can appear only as diagnostic refs.
- Raw prompt/response persistence fails.
- Import-boundary tests reject SDK/framework static imports outside adapter modules.
