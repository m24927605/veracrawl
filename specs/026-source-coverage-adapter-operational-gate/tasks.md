# Tasks: VeraCrawl Source Coverage Adapter Operational Gate

**Input**: Design documents from `specs/026-source-coverage-adapter-operational-gate/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Phase 1: Setup

- [x] T001 Run Spec Kit prerequisite check for 026 feature context
- [x] T002 Add `veracrawl-source-coverage` CLI entry point in `pyproject.toml`

## Phase 2: Foundational Contracts

- [x] T003 Extend source coverage enums in `src/veracrawl/contracts/enums.py`
- [x] T004 Add source coverage contracts in `src/veracrawl/contracts/source_coverage.py`
- [x] T005 Export contracts in `src/veracrawl/contracts/__init__.py`
- [x] T006 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T007 Update registry expectations in `tests/contract/test_contract_registry.py`

## Phase 3: User Story 1 - Complete Source Adapter Mapping

- [x] T008 [P] [US1] Add contract tests in `tests/contract/test_source_coverage_contracts.py`
- [x] T009 [P] [US1] Add registry tests in `tests/contract/test_source_coverage_contract_registry.py`
- [x] T010 [P] [US1] Add fixture assertion helper in `tests/helpers/source_coverage_fixture_assertions.py`
- [x] T011 [US1] Add adapter-owned deterministic source coverage descriptor in `src/veracrawl/adapters/source_coverage/contract.py`
- [x] T012 [US1] Implement gate runtime in `src/veracrawl/fetch/source_coverage_gate.py`
- [x] T013 [US1] Implement CLI runner in `src/veracrawl/cli/source_coverage.py`
- [x] T014 [US1] Add `source-coverage-adapter-success` fixture/oracles
- [x] T015 [US1] Add success integration test

## Phase 4: User Story 2 - Missing Live Runtime Needs Review

- [x] T016 [P] [US2] Add import-boundary test
- [x] T017 [P] [US2] Add `source-coverage-adapter-runtime-unavailable` fixture/oracles
- [x] T018 [US2] Implement runtime-unavailable needs-review behavior
- [x] T019 [US2] Add needs-review integration coverage

## Phase 5: User Story 3 - Negative Source Mappings

- [x] T020 [P] [US3] Add negative fixture/oracles
- [x] T021 [P] [US3] Add negative unit tests
- [x] T022 [US3] Implement negative failure scenarios
- [x] T023 [US3] Add negative integration assertions

## Phase 6: Documentation And Acceptance

- [x] T024 Update README and docs/07, docs/09, docs/10, docs/11
- [x] T025 Update `AGENTS.md` active Spec Kit block for 026
- [x] T026 Run registry validation, ruff, mypy, focused tests, CLI fixtures, and full test suite
- [x] T027 Record real verification results in this `tasks.md`

## Validation Record

- `uv lock`: passed, resolved 30 packages.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json`: passed with `"ok": true`.
- `uv run --python python3.12 --extra dev ruff check src tests`: passed.
- `uv run --python python3.12 --extra dev mypy src`: passed, 186 source files checked.
- Focused 026 tests: `uv run --python python3.12 --extra dev pytest tests/contract/test_source_coverage_contracts.py tests/contract/test_source_coverage_contract_registry.py tests/contract/test_source_coverage_import_boundaries.py tests/unit/test_source_coverage_gate.py tests/integration/test_source_coverage_fixtures.py`: 17 passed.
- Source coverage CLI fixture loop for all 11 fixtures: passed.
- Full non-Docker suite: `uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration`: 469 passed, 5 skipped.
- Full Docker-backed suite: `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/contract tests/unit tests/integration`: 474 passed.
