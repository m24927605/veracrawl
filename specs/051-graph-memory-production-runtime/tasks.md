# Tasks: Graph And Memory Production Runtime

**Input**: Design documents from `/specs/051-graph-memory-production-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add graph/memory production failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add graph/memory production contracts in `src/veracrawl/contracts/graph_memory.py`
- [x] T003 Export graph/memory production contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target coverage in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_graph_memory_production_contracts.py`
- [x] T006 [P] Add registry tests in `tests/contract/test_graph_memory_production_contract_registry.py`
- [x] T007 [P] Add import boundary tests in `tests/contract/test_graph_memory_production_import_boundaries.py`

## Phase 2: Runtime And CLI

- [x] T008 Implement graph/memory production runtime in `src/veracrawl/graph_memory/runtime.py`
- [x] T009 Add graph/memory package exports in `src/veracrawl/graph_memory/__init__.py`
- [x] T010 Implement replay validation in `src/veracrawl/review_replay/graph_memory.py`
- [x] T011 Implement fixture CLI in `src/veracrawl/cli/graph_memory_runtime.py`
- [x] T012 Register CLI entry point in `pyproject.toml`
- [x] T013 [P] Add runtime unit tests in `tests/unit/test_graph_memory_production_runtime.py`
- [x] T014 [P] Add replay unit tests in `tests/unit/test_graph_memory_production_replay.py`

## Phase 3: Fixtures

- [x] T015 [P] Add production success fixture in `tests/fixtures/graph-memory-production-success`
- [x] T016 [P] Add frontier priority success fixture in `tests/fixtures/graph-memory-frontier-priority-success`
- [x] T017 [P] Add repair explanation success fixture in `tests/fixtures/graph-memory-repair-explanation-success`
- [x] T018 [P] Add missing live normalization fixture in `tests/fixtures/graph-memory-missing-live-normalization`
- [x] T019 [P] Add missing live evidence fixture in `tests/fixtures/graph-memory-missing-live-evidence`
- [x] T020 [P] Add missing multi-agent fixture in `tests/fixtures/graph-memory-missing-multi-agent`
- [x] T021 [P] Add graph-as-evidence fixture in `tests/fixtures/graph-memory-graph-as-evidence`
- [x] T022 [P] Add memory-as-evidence fixture in `tests/fixtures/graph-memory-memory-as-evidence`
- [x] T023 [P] Add stale memory fixture in `tests/fixtures/graph-memory-stale-memory`
- [x] T024 [P] Add missing invalidation fixture in `tests/fixtures/graph-memory-missing-invalidation`
- [x] T025 [P] Add missing frontier explanation fixture in `tests/fixtures/graph-memory-missing-frontier-explanation`
- [x] T026 [P] Add replay mismatch fixture in `tests/fixtures/graph-memory-replay-mismatch`
- [x] T027 [P] Add fixture helper assertions in `tests/helpers/graph_memory_production_fixture_assertions.py`
- [x] T028 [P] Add fixture integration tests in `tests/integration/test_graph_memory_production_fixtures.py`

## Phase 4: Docs

- [x] T029 [P] Update `README.md`
- [x] T030 [P] Update `docs/07-data-contracts.md`
- [x] T031 [P] Update `docs/08-build-roadmap.md`
- [x] T032 [P] Update `docs/09-target-capability-model.md`
- [x] T033 [P] Update `docs/10-target-implementation-design.md`
- [x] T034 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T035 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T036 Run Spec Kit prerequisite check
- [x] T037 Run `uv lock`
- [x] T038 Run ruff
- [x] T039 Run mypy
- [x] T040 Run registry validation
- [x] T041 Run focused row 051 tests
- [x] T042 Run row 051 CLI fixture loop
- [x] T043 Run full non-Docker pytest gate
- [x] T044 Run Docker-backed pytest gate
- [x] T045 Run `git diff --check`
- [x] T046 Record validation results

## Validation Results

- Spec Kit prerequisite: passed for `specs/051-graph-memory-production-runtime`.
- `uv lock`: resolved 30 packages.
- `ruff check .`: passed.
- Focused mypy: passed for `src`, row 051 contract/unit/integration tests, helpers, and registry tests; 253 source files checked.
- Registry validation: `ok=true`, no errors.
- Focused pytest: 26 passed.
- `veracrawl-graph-memory-runtime` CLI loop: 12 fixtures passed.
- Full non-Docker pytest: 971 passed, 5 skipped.
- Docker-backed pytest: 976 passed.
- `git diff --check`: passed.
