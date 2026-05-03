# Tasks: Real-World Benchmark Corpus Gate

**Input**: Design documents from `/specs/055-real-world-benchmark-corpus/`

## Phase 1: Roadmap And Contracts

- [x] T001 Amend `specs/038-production-runtime-closure/spec.md` to include 055 as the approved post-release real-world benchmark validation spec.
- [x] T002 Amend `docs/08-build-roadmap.md` to include 055 and its completion gate.
- [x] T003 Add `.veracrawl-real-runs/` to `.gitignore`.
- [x] T004 Add real-world benchmark failure enum in `src/veracrawl/contracts/enums.py`.
- [x] T005 Add real-world benchmark contracts in `src/veracrawl/contracts/real_world_benchmark.py`.
- [x] T006 Export real-world benchmark contracts in `src/veracrawl/contracts/__init__.py`.
- [x] T007 Register contracts, commands, events, fixture oracle, and target area in `src/veracrawl/contracts/registry.py`.
- [x] T008 [P] Add contract tests in `tests/contract/test_real_world_benchmark_contracts.py`.
- [x] T009 [P] Add registry tests in `tests/contract/test_real_world_benchmark_contract_registry.py`.
- [x] T010 [P] Add import boundary tests in `tests/contract/test_real_world_benchmark_import_boundaries.py`.

## Phase 2: Runtime And Replay

- [x] T011 Add benchmark package in `src/veracrawl/benchmarks/__init__.py`.
- [x] T012 Implement real-world benchmark runtime in `src/veracrawl/benchmarks/real_world.py`.
- [x] T013 Implement replay validation in `src/veracrawl/review_replay/real_world_benchmark.py`.
- [x] T014 [P] Add runtime unit tests in `tests/unit/test_real_world_benchmark_runtime.py`.
- [x] T015 [P] Add replay unit tests in `tests/unit/test_real_world_benchmark_replay.py`.

## Phase 3: CLI And Corpus Fixture

- [x] T016 Implement CLI in `src/veracrawl/cli/real_benchmark.py`.
- [x] T017 Register CLI entry point in `pyproject.toml`.
- [x] T018 Add public corpus fixture in `tests/fixtures/real-world-public-corpus`.
- [x] T019 [P] Add fixture integration tests in `tests/integration/test_real_world_benchmark_fixtures.py`.

## Phase 4: Docs

- [x] T020 Update `docs/07-data-contracts.md`.
- [x] T021 Update `docs/10-target-implementation-design.md`.
- [x] T022 Update `docs/11-target-testing-and-acceptance.md`.
- [x] T023 Update `README.md`.
- [x] T024 Update `AGENTS.md` active Spec Kit pointer.

## Phase 5: Verification

- [x] T025 Run Spec Kit prerequisite check.
- [x] T026 Run `uv lock`.
- [x] T027 Run ruff.
- [x] T028 Run mypy.
- [x] T029 Run registry validation.
- [x] T030 Run focused row 055 tests.
- [x] T031 Run real public corpus CLI gate.
- [x] T032 Run full non-Docker pytest gate.
- [x] T033 Run Docker-backed pytest gate.
- [x] T034 Run `git diff --check`.
- [x] T035 Record validation results.

## Validation Results

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  passed for `specs/055-real-world-benchmark-corpus`.
- `uv lock` resolved successfully.
- `uv run --python python3.12 --extra dev ruff check .`: all checks passed.
- `uv run --python python3.12 --extra dev mypy src ...`: success across 268
  source files.
- `uv run --python python3.12 --extra dev python -m veracrawl.cli.contracts
  validate --format json`: registry validation returned `ok: true`.
- Focused row 055 pytest gate: 21 passed in 0.80s.
- Real public corpus CLI gate:
  `veracrawl-real-benchmark run tests/fixtures/real-world-public-corpus
  --profile target --out .veracrawl-real-runs/real-world-public-corpus`
  returned `completion_result=pass`, `operator_status=real_world_benchmark_completed`,
  `site_count=4`, `artifact_count=4`, and `replay_bundle_count=4`.
- Full non-Docker pytest gate: 1041 passed, 5 skipped in 54.50s.
- Docker-backed pytest gate with Postgres, Redis, S3, and infrastructure extras:
  1046 passed in 82.61s.
- `git diff --check`: passed.
