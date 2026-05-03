# Tasks: Worker Orchestration And Scale Runtime

**Input**: Design documents from `/specs/052-worker-orchestration-scale-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add worker orchestration failure enum and worker pool values in `src/veracrawl/contracts/enums.py`
- [x] T002 Add worker orchestration contracts in `src/veracrawl/contracts/scale.py`
- [x] T003 Export worker orchestration contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target coverage in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_worker_orchestration_contracts.py`
- [x] T006 [P] Add registry tests in `tests/contract/test_worker_orchestration_contract_registry.py`
- [x] T007 [P] Add import boundary tests in `tests/contract/test_worker_orchestration_import_boundaries.py`

## Phase 2: Runtime And CLI

- [x] T008 Implement worker orchestration runtime in `src/veracrawl/scale/worker_orchestration.py`
- [x] T009 Implement replay validation in `src/veracrawl/review_replay/worker_orchestration.py`
- [x] T010 Implement fixture CLI in `src/veracrawl/cli/worker_orchestration.py`
- [x] T011 Register CLI entry point in `pyproject.toml`
- [x] T012 [P] Add runtime unit tests in `tests/unit/test_worker_orchestration_runtime.py`
- [x] T013 [P] Add replay unit tests in `tests/unit/test_worker_orchestration_replay.py`

## Phase 3: Fixtures

- [x] T014 [P] Add production success fixture in `tests/fixtures/worker-orchestration-production-success`
- [x] T015 [P] Add worker crash recovered fixture in `tests/fixtures/worker-orchestration-worker-crash-recovered`
- [x] T016 [P] Add backpressure/autoscale success fixture in `tests/fixtures/worker-orchestration-backpressure-autoscale-success`
- [x] T017 [P] Add missing persistence fixture in `tests/fixtures/worker-orchestration-missing-persistence`
- [x] T018 [P] Add missing queue broker fixture in `tests/fixtures/worker-orchestration-missing-queue-broker`
- [x] T019 [P] Add unrecovered stale lease fixture in `tests/fixtures/worker-orchestration-stale-lease-unrecovered`
- [x] T020 [P] Add missing heartbeat fixture in `tests/fixtures/worker-orchestration-missing-heartbeat`
- [x] T021 [P] Add hidden dead-letter fixture in `tests/fixtures/worker-orchestration-dead-letter-hidden`
- [x] T022 [P] Add duplicate pollution fixture in `tests/fixtures/worker-orchestration-duplicate-pollution`
- [x] T023 [P] Add backpressure without policy fixture in `tests/fixtures/worker-orchestration-backpressure-without-policy`
- [x] T024 [P] Add replay mismatch fixture in `tests/fixtures/worker-orchestration-replay-mismatch`
- [x] T025 [P] Add fixture helper assertions in `tests/helpers/worker_orchestration_fixture_assertions.py`
- [x] T026 [P] Add fixture integration tests in `tests/integration/test_worker_orchestration_fixtures.py`

## Phase 4: Docs

- [x] T027 [P] Update `README.md`
- [x] T028 [P] Update `docs/07-data-contracts.md`
- [x] T029 [P] Update `docs/08-build-roadmap.md`
- [x] T030 [P] Update `docs/10-target-implementation-design.md`
- [x] T031 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T032 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T033 Run Spec Kit prerequisite check
- [x] T034 Run `uv lock`
- [x] T035 Run ruff
- [x] T036 Run mypy
- [x] T037 Run registry validation
- [x] T038 Run focused row 052 tests
- [x] T039 Run row 052 CLI fixture loop
- [x] T040 Run full non-Docker pytest gate
- [x] T041 Run Docker-backed pytest gate
- [x] T042 Run `git diff --check`
- [x] T043 Record validation results

## Validation Results

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`: passed; feature dir `specs/052-worker-orchestration-scale-runtime` and research/data-model/contracts/quickstart/tasks docs present.
- `uv lock`: passed; resolved 30 packages.
- `uv run --python python3.12 --extra dev ruff check .`: passed.
- `uv run --python python3.12 --extra dev mypy src tests/contract/test_worker_orchestration_contracts.py tests/contract/test_worker_orchestration_contract_registry.py tests/contract/test_worker_orchestration_import_boundaries.py tests/unit/test_worker_orchestration_runtime.py tests/unit/test_worker_orchestration_replay.py tests/integration/test_worker_orchestration_fixtures.py tests/helpers/worker_orchestration_fixture_assertions.py tests/contract/test_contract_registry.py`: passed; 256 source files checked.
- `uv run --python python3.12 --extra dev python -m veracrawl.cli.contracts validate --format json`: passed; `ok=true` with no registry errors.
- Focused row 052 pytest suite: passed; 23 passed.
- `veracrawl-worker-orchestration` CLI loop over `tests/fixtures/worker-orchestration-*`: passed; 11 fixtures.
- `uv run --python python3.12 --extra dev pytest`: passed; 989 passed, 5 skipped.
- `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`: passed; 994 passed.
- `git diff --check`: passed.
