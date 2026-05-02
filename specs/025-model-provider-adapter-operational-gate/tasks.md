# Tasks: VeraCrawl Model Provider Adapter Operational Gate

**Input**: Design documents from `specs/025-model-provider-adapter-operational-gate/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Phase 1: Setup

- [x] T001 Run Spec Kit prerequisite check for 025 feature context
- [x] T002 Add `veracrawl-model-providers` CLI entry point in `pyproject.toml`

## Phase 2: Foundational Contracts

- [x] T003 Extend model provider adapter enums in `src/veracrawl/contracts/enums.py`
- [x] T004 Add model provider adapter contracts in `src/veracrawl/contracts/model_provider_adapter.py`
- [x] T005 Export contracts in `src/veracrawl/contracts/__init__.py`
- [x] T006 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T007 Update registry expectations in `tests/contract/test_contract_registry.py`

## Phase 3: User Story 1 - Canonical Provider Mapping

- [x] T008 [P] [US1] Add contract tests in `tests/contract/test_model_provider_adapter_contracts.py`
- [x] T009 [P] [US1] Add registry tests in `tests/contract/test_model_provider_adapter_contract_registry.py`
- [x] T010 [P] [US1] Add fixture assertion helper in `tests/helpers/model_provider_adapter_fixture_assertions.py`
- [x] T011 [US1] Add adapter-owned deterministic provider contract adapter in `src/veracrawl/adapters/model_providers/contract.py`
- [x] T012 [US1] Implement gate runtime in `src/veracrawl/agents/model_provider_gate.py`
- [x] T013 [US1] Implement CLI runner in `src/veracrawl/cli/model_providers.py`
- [x] T014 [US1] Add `model-provider-adapter-success` fixture/oracles
- [x] T015 [US1] Add success integration test

## Phase 4: User Story 2 - Missing Live Provider Needs Review

- [x] T016 [P] [US2] Add import-boundary test
- [x] T017 [P] [US2] Add `model-provider-adapter-runtime-unavailable` fixture/oracles
- [x] T018 [US2] Implement runtime-unavailable needs-review behavior
- [x] T019 [US2] Add needs-review integration coverage

## Phase 5: User Story 3 - Negative Provider Mappings

- [x] T020 [P] [US3] Add negative fixture/oracles
- [x] T021 [P] [US3] Add negative unit tests
- [x] T022 [US3] Implement negative failure scenarios
- [x] T023 [US3] Add negative integration assertions

## Phase 6: Documentation And Acceptance

- [x] T024 Update README and docs/07, docs/09, docs/10, docs/11
- [x] T025 Update `AGENTS.md` active Spec Kit block for 025
- [x] T026 Run registry validation, ruff, mypy, focused tests, CLI fixtures, and full test suite
- [x] T027 Record real verification results in this `tasks.md`

## Validation Record

- 2026-05-03: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` completed before implementation.
- 2026-05-03: `uv lock` completed.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` returned registry validation `ok: true` with no errors or warnings.
- 2026-05-03: `uv run --python python3.12 --extra dev ruff check src tests` passed.
- 2026-05-03: `uv run --python python3.12 --extra dev mypy src` passed with no issues in 181 source files.
- 2026-05-03: Focused 025 pytest suite passed: 16 passed.
- 2026-05-03: All 10 `veracrawl-model-providers run` fixtures completed with expected results: success `pass`, runtime unavailable `needs_review`, and eight negative fixtures `fail`.
- 2026-05-03: Full non-Docker suite passed: 452 passed, 5 skipped.
- 2026-05-03: Docker-backed full suite passed with Postgres, Redis/Valkey, S3/MinIO, infrastructure, and DR live gates enabled: 457 passed.
