# Tasks: VeraCrawl Temporal KG Identity Projection Gate

**Input**: Design documents from `/specs/029-temporal-kg-identity-projection-gate/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature implements temporal KG contracts, deterministic runtime gate behavior, fixture/oracle validation, evidence boundary checks, replay checks, and import boundaries.

## Phase 1: Setup

- [x] T001 Add `veracrawl-temporal-kg` console script target in `pyproject.toml`
- [x] T002 [P] Create temporal KG CLI module in `src/veracrawl/cli/temporal_kg.py`
- [x] T003 [P] Create temporal KG runtime in `src/veracrawl/graph/temporal_kg.py`

## Phase 2: Foundational

- [x] T004 [P] Add temporal KG enums in `src/veracrawl/contracts/enums.py`
- [x] T005 [P] Add temporal KG contracts in `src/veracrawl/contracts/graph.py`
- [x] T006 Export temporal KG contracts in `src/veracrawl/contracts/__init__.py`
- [x] T007 Extend registry for temporal KG contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`
- [x] T008 [P] Write temporal KG contract tests in `tests/contract/test_temporal_kg_contracts.py`
- [x] T009 [P] Write temporal KG registry tests in `tests/contract/test_temporal_kg_contract_registry.py`
- [x] T010 [P] Write import-boundary tests in `tests/contract/test_temporal_kg_import_boundaries.py`

## Phase 3: Runtime And Fixtures

- [x] T011 [P] Write temporal KG unit gate tests in `tests/unit/test_temporal_kg_gate.py`
- [x] T012 [P] Create fixture assertion helpers in `tests/helpers/temporal_kg_fixture_assertions.py`
- [x] T013 Create success fixtures for projection, false merge, and false split
- [x] T014 Create needs-review and negative fixtures
- [x] T015 Implement success, needs-review, and negative runtime behavior
- [x] T016 Implement CLI fixture validation and `run_report.json` writing
- [x] T017 [P] Write integration fixture tests in `tests/integration/test_temporal_kg_fixtures.py`

## Phase 4: Docs And Verification

- [x] T018 [P] Update temporal KG usage notes in `README.md`
- [x] T019 [P] Update temporal KG executable contracts in `docs/07-data-contracts.md`
- [x] T020 [P] Update graph intelligence capability notes in `docs/09-target-capability-model.md`
- [x] T021 [P] Update implementation design notes in `docs/10-target-implementation-design.md`
- [x] T022 [P] Update target testing and acceptance notes in `docs/11-target-testing-and-acceptance.md`
- [x] T023 [P] Update active Spec Kit pointer in `AGENTS.md`
- [x] T024 Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- [x] T025 Run `uv lock`
- [x] T026 Run `uv run --python python3.12 --extra dev ruff check src tests`
- [x] T027 Run `uv run --python python3.12 --extra dev mypy src`
- [x] T028 Run `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json`
- [x] T029 Run focused temporal KG tests
- [x] T030 Run temporal KG CLI fixture loop from `quickstart.md`
- [x] T031 Run full non-Docker `pytest tests/contract tests/unit tests/integration`
- [x] T032 Run Docker-backed full pytest gate when dependencies are available
- [x] T033 Run `git diff --check` and record validation results

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/029-temporal-kg-identity-projection-gate`.
- Dependency lock: `uv lock` passed.
- Quality gates: `ruff check src tests` passed; `mypy src` passed with 193 source files checked.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- Focused tests: `tests/contract/test_temporal_kg_contracts.py`, `tests/contract/test_temporal_kg_contract_registry.py`, `tests/contract/test_temporal_kg_import_boundaries.py`, `tests/unit/test_temporal_kg_gate.py`, and `tests/integration/test_temporal_kg_fixtures.py` passed with 22 tests.
- CLI fixtures: `temporal-kg-projection-success`, `temporal-kg-false-merge-adjudicated`, `temporal-kg-false-split-superseded`, `temporal-kg-runtime-unavailable`, `temporal-kg-provisional-identity`, `temporal-kg-projection-as-evidence`, `temporal-kg-missing-canonical-source`, `temporal-kg-missing-bitemporal-refs`, `temporal-kg-false-merge-without-adjudication`, `temporal-kg-false-split-without-supersession`, and `temporal-kg-missing-replay` all passed declared oracles through `veracrawl-temporal-kg run`.
- Full non-Docker suite: `uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration` passed with `528 passed, 5 skipped`.
- Docker-backed suite: `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/contract tests/unit tests/integration` passed with `533 passed`.
- Diff hygiene: `git diff --check` passed.
