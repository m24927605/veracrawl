# Implementation Plan: VeraCrawl Source Coverage Adapter Operational Gate

**Branch**: `026-source-coverage-adapter-operational-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/026-source-coverage-adapter-operational-gate/spec.md`

## Summary

Implement an adapter-owned source coverage gate that validates canonical mapping from all target source adapter families into VeraCrawl contracts. The gate remains core-neutral, uses dynamic adapter loading in CLI, returns `needs_review` for missing live runtime/credential/parser/browser/API refs, and fails unsafe or incomplete mappings.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic, argparse, pytest, ruff, mypy
**Storage**: deterministic fixture run reports under `.veracrawl-test-runs/`
**Testing**: pytest contract/unit/integration, CLI fixture/oracle loop, registry validation, ruff, mypy, Docker-backed full suite
**Target Platform**: local deterministic fixture runner; future concrete source runtimes stay optional
**Project Type**: Python library/CLI
**Performance Goals**: deterministic fixtures complete in CI-scale time
**Constraints**: no core static imports of browser/parser/vault/API/source runtime SDKs; no raw secret persistence; no adapter-native canonical state
**Scale/Scope**: materializes source coverage contracts, runtime, CLI, fixtures, and docs; does not call external websites/APIs
**VeraCrawl Owner Services**: ports, fetch, browser, control, policy, review_replay, ops, tests
**Canonical Contracts**: SourceAdapterSpec, SourceAdapterResult, FetchAttempt, PageSnapshot, BrowserInteractionStep, CredentialUseAudit, DocumentArtifact, CommandResult, ObservabilityReport, SecurityPrivacyReport
**Replay/Artifact Impact**: replay bundle refs, event cursor refs, command refs, outbox refs, source result refs, natural result refs
**Security/Policy Impact**: source scope, credential isolation, browser side-effect blocking, privacy lifecycle, replay completeness

## Constitution Check

- [x] General-purpose AI agent crawler capability is preserved; adapters map into common source contracts.
- [x] Python remains the implementation language.
- [x] Agent/model/provider/runtime boundaries remain framework-neutral and SDK-neutral.
- [x] Low coupling/high cohesion boundaries are explicit through contracts, runtime gate, adapter package, CLI, fixtures, and tests.
- [x] Evidence, verification, publication, replay, and artifact lineage are not weakened.
- [x] Security, policy, credential, prompt-injection, browser, privacy lifecycle, and replay gates are defined.
- [x] Command payload schemas, event payload schemas, fixture/oracle tests, and negative tests are planned before implementation.
- [x] Target architecture is not weakened due to staffing, schedule, sprint pressure, or delivery speed.

## Project Structure

```text
specs/026-source-coverage-adapter-operational-gate/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── boundary.md
│   └── source-coverage-gate.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

```text
src/veracrawl/
├── adapters/source_coverage/contract.py
├── fetch/source_coverage_gate.py
├── cli/source_coverage.py
└── contracts/source_coverage.py

tests/
├── contract/test_source_coverage_contracts.py
├── contract/test_source_coverage_contract_registry.py
├── contract/test_source_coverage_import_boundaries.py
├── unit/test_source_coverage_gate.py
├── helpers/source_coverage_fixture_assertions.py
└── integration/test_source_coverage_fixtures.py
```

**Structure Decision**: Keep contracts, core gate runtime, adapter-owned deterministic source coverage descriptors, CLI runner, fixtures, and tests separated. CLI may dynamically import adapter packages; core must not import concrete source/browser/parser/vault/API modules.

## Acceptance Gates

- Registry validation includes source coverage contracts/events/fixtures.
- Import-boundary tests reject forbidden SDK imports in core and static adapter imports in CLI.
- Success fixture passes only with all target source adapter families.
- Runtime-unavailable fixture returns `needs_review`.
- Negative fixtures fail deterministically.
- Full test suite and Docker-backed live operational gates remain green.
