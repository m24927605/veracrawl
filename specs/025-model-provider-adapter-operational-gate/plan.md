# Implementation Plan: VeraCrawl Model Provider Adapter Operational Gate

**Branch**: `025-model-provider-adapter-operational-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/025-model-provider-adapter-operational-gate/spec.md`

## Summary

Implement an adapter-owned model provider gate that validates canonical mapping from model provider adapters into VeraCrawl contracts. The gate remains provider-neutral in core, uses dynamic adapter loading in CLI, returns `needs_review` for missing live provider runtime/API credentials, and fails unsafe or incomplete mappings.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Pydantic, Typer-free argparse CLI, pytest, ruff, mypy  
**Storage**: deterministic fixture run reports under `.veracrawl-test-runs/`  
**Testing**: pytest contract/unit/integration, CLI fixture/oracle loop, registry validation, ruff, mypy, Docker-backed full suite  
**Target Platform**: local deterministic fixture runner; future concrete SDK adapters stay optional  
**Project Type**: Python library/CLI  
**Performance Goals**: deterministic fixtures complete in CI-scale time  
**Constraints**: no core static imports of model provider SDKs; no raw prompt/response/credential persistence; no provider-native canonical transcript state  
**Scale/Scope**: materializes provider gate contracts, runtime, CLI, fixtures, and docs; does not call external model APIs  
**VeraCrawl Owner Services**: agents, policy, review_replay, ops, tests  
**Canonical Contracts**: ModelRequest, ModelResponse, ModelCallTrace, ContextBundleTrace, AgentRunRequest, AgentRunResult, AgentActionTrace, CommandResult, ObservabilityReport, SecurityPrivacyReport  
**Replay/Artifact Impact**: replay bundle refs, event cursor refs, command refs, outbox refs, trace refs  
**Security/Policy Impact**: prompt redaction, credential isolation, unsafe tool suggestion blocking, provider transcript boundary

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; provider adapters map into common contracts.
- [x] Python remains the implementation language.
- [x] Agent runtime remains framework-neutral and provider-neutral; model SDKs are isolated behind replaceable adapters.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, runtime gate, adapter package, CLI, fixtures, and tests.
- [x] Evidence, verification, publication, replay, and artifact lineage are not weakened; model output is not source evidence.
- [x] Security, policy, credential, prompt-injection, privacy lifecycle, and replay gates are defined.
- [x] Command payload schemas, event payload schemas, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

### Documentation

```text
specs/025-model-provider-adapter-operational-gate/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── boundary.md
│   └── model-provider-gate.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code

```text
src/veracrawl/
├── adapters/model_providers/contract.py
├── agents/model_provider_gate.py
├── cli/model_providers.py
└── contracts/model_provider_adapter.py

tests/
├── contract/test_model_provider_adapter_contracts.py
├── contract/test_model_provider_adapter_contract_registry.py
├── contract/test_model_provider_adapter_import_boundaries.py
├── unit/test_model_provider_adapter_gate.py
├── helpers/model_provider_adapter_fixture_assertions.py
└── integration/test_model_provider_adapter_fixtures.py
```

**Structure Decision**: Keep contracts, core gate runtime, adapter-owned deterministic provider descriptors, CLI runner, fixtures, and tests separated. CLI may dynamically import adapter packages; core must not import provider SDKs or adapter modules.

## Implementation Phases

1. Create spec artifacts and requirement checklist.
2. Add model provider adapter contracts/enums and registry entries.
3. Add contract, registry, import-boundary, unit, and integration tests.
4. Add adapter-owned deterministic contract provider adapters.
5. Implement core provider gate runtime and CLI runner.
6. Add success, no-runtime, and negative fixtures/oracles.
7. Update docs and AGENTS active Spec Kit block.
8. Run registry validation, ruff, mypy, focused tests, CLI fixtures, full tests, and Docker-backed full suite.

## Acceptance Gates

- Registry validation includes model provider adapter contracts/events/fixtures.
- Import-boundary tests reject provider SDK imports in core and CLI static imports.
- Success fixture passes only with all provider family refs.
- Runtime-unavailable fixture returns `needs_review`.
- Negative fixtures fail deterministically.
- Full test suite and Docker-backed live operational gates remain green.
