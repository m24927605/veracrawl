# Tasks: VeraCrawl Dynamic Source Adapter Runtime Foundation

**Input**: Design documents from `specs/027-dynamic-source-adapter-runtime-foundation/`

## Phase 1: Setup

- [x] T001 Run Spec Kit prerequisite check for 027 feature context
- [x] T002 Add `veracrawl-source-runtime` CLI entry point in `pyproject.toml`

## Phase 2: Foundational Contracts

- [x] T003 Extend dynamic source runtime failure enums in `src/veracrawl/contracts/enums.py`
- [x] T004 Add dynamic source runtime contracts in `src/veracrawl/contracts/source_runtime.py`
- [x] T005 Export contracts in `src/veracrawl/contracts/__init__.py`
- [x] T006 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T007 Update registry expectations in `tests/contract/test_contract_registry.py`

## Phase 3: Complete Runtime

- [x] T008 Add contract tests in `tests/contract/test_dynamic_source_runtime_contracts.py`
- [x] T009 Add registry tests in `tests/contract/test_dynamic_source_runtime_contract_registry.py`
- [x] T010 Add fixture assertion helper in `tests/helpers/dynamic_source_runtime_fixture_assertions.py`
- [x] T011 Add adapter-owned deterministic/local runtime builder in `src/veracrawl/adapters/sources/dynamic_runtime.py`
- [x] T012 Implement core runtime gate in `src/veracrawl/fetch/dynamic_source_runtime.py`
- [x] T013 Implement CLI runner in `src/veracrawl/cli/source_runtime.py`
- [x] T014 Add success fixture/oracles
- [x] T015 Add success integration test

## Phase 4: Needs Review And Negative Cases

- [x] T016 Add import-boundary test
- [x] T017 Add runtime-unavailable fixture/oracles
- [x] T018 Add negative fixture/oracles
- [x] T019 Add negative unit tests
- [x] T020 Add negative integration assertions

## Phase 5: Documentation And Acceptance

- [x] T021 Update README and docs/07, docs/09, docs/10, docs/11
- [x] T022 Update `AGENTS.md` active Spec Kit block for 027
- [x] T023 Run registry validation, ruff, mypy, focused tests, CLI fixtures, and full suites
- [x] T024 Record real verification results in this `tasks.md`

## Validation Record

- `uv lock` -> passed.
- `uv run --python python3.12 --extra dev ruff check src tests` -> passed.
- `uv run --python python3.12 --extra dev mypy src` -> passed; 189 source files checked.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` -> passed; registry validation ok.
- `uv run --python python3.12 --extra dev pytest tests/contract/test_dynamic_source_runtime_contracts.py tests/contract/test_dynamic_source_runtime_contract_registry.py tests/contract/test_dynamic_source_runtime_import_boundaries.py tests/unit/test_dynamic_source_runtime_gate.py tests/integration/test_dynamic_source_runtime_fixtures.py` -> 18 passed.
- 10-fixture `veracrawl-source-runtime run ... --profile target` loop -> passed for success, runtime-unavailable, and 8 negative fixtures.
- `uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration` -> 487 passed, 5 skipped.
- `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/contract tests/unit tests/integration` -> 492 passed.
- `git diff --check` -> passed.
