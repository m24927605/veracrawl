# Tasks: Production Benchmark And Release Gate

**Input**: Design documents from `/specs/054-production-benchmark-release-gate/`

## Phase 1: Contracts And Registry

- [x] T001 Add production release failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add row 054 contracts in `src/veracrawl/contracts/release.py`
- [x] T003 Export row 054 contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target coverage in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_production_benchmark_release_contracts.py`
- [x] T006 [P] Add registry tests in `tests/contract/test_production_benchmark_release_contract_registry.py`
- [x] T007 [P] Add import boundary tests in `tests/contract/test_production_benchmark_release_import_boundaries.py`

## Phase 2: Runtime And CLI

- [x] T008 Implement production benchmark release runtime in `src/veracrawl/release/benchmark_gate.py`
- [x] T009 Implement replay validation in `src/veracrawl/review_replay/release_gate.py`
- [x] T010 Implement fixture CLI in `src/veracrawl/cli/release_gate.py`
- [x] T011 Register CLI entry point in `pyproject.toml`
- [x] T012 [P] Add runtime unit tests in `tests/unit/test_production_benchmark_release_gate.py`
- [x] T013 [P] Add replay unit tests in `tests/unit/test_production_benchmark_release_replay.py`

## Phase 3: Fixtures

- [x] T014 [P] Add benchmark success fixture in `tests/fixtures/production-release-benchmark-success`
- [x] T015 [P] Add missing target runtime fixture in `tests/fixtures/production-release-missing-target-runtime`
- [x] T016 [P] Add missing source coverage fixture in `tests/fixtures/production-release-missing-source-coverage`
- [x] T017 [P] Add missing product acceptance fixture in `tests/fixtures/production-release-missing-product-acceptance`
- [x] T018 [P] Add missing security/privacy fixture in `tests/fixtures/production-release-missing-security-privacy`
- [x] T019 [P] Add missing publication fixture in `tests/fixtures/production-release-missing-publication`
- [x] T020 [P] Add missing worker orchestration fixture in `tests/fixtures/production-release-missing-worker-orchestration`
- [x] T021 [P] Add missing ops runtime fixture in `tests/fixtures/production-release-missing-ops-runtime`
- [x] T022 [P] Add SLO violation fixture in `tests/fixtures/production-release-slo-violation`
- [x] T023 [P] Add release blocker fixture in `tests/fixtures/production-release-blocker-present`
- [x] T024 [P] Add false-ready fixture in `tests/fixtures/production-release-false-ready`
- [x] T025 [P] Add replay mismatch fixture in `tests/fixtures/production-release-replay-mismatch`
- [x] T026 [P] Add fixture helper assertions in `tests/helpers/production_benchmark_release_fixture_assertions.py`
- [x] T027 [P] Add fixture integration tests in `tests/integration/test_production_benchmark_release_fixtures.py`

## Phase 4: Docs

- [x] T028 [P] Update `README.md`
- [x] T029 [P] Update `docs/07-data-contracts.md`
- [x] T030 [P] Update `docs/08-build-roadmap.md`
- [x] T031 [P] Update `docs/10-target-implementation-design.md`
- [x] T032 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T033 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T034 Run Spec Kit prerequisite check
- [x] T035 Run `uv lock`
- [x] T036 Run ruff
- [x] T037 Run mypy
- [x] T038 Run registry validation
- [x] T039 Run focused row 054 tests
- [x] T040 Run row 054 CLI fixture loop
- [x] T041 Run full non-Docker pytest gate
- [x] T042 Run Docker-backed pytest gate
- [x] T043 Run `git diff --check`
- [x] T044 Record validation results

## Validation Results

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  passed for `specs/054-production-benchmark-release-gate`.
- `uv lock` resolved successfully.
- `uv run --python python3.12 --extra dev ruff check .`: all checks passed.
- `uv run --python python3.12 --extra dev mypy src ...`: success across 264
  source files.
- `uv run --python python3.12 --extra dev python -m veracrawl.cli.contracts
  validate --format json`: registry validation returned `ok: true`.
- Focused row 054 pytest gate: 23 passed in 0.63s.
- `veracrawl-release-gate` CLI fixture loop: 12 production release fixtures
  passed.
- Full non-Docker pytest gate: 1025 passed, 5 skipped in 55.19s.
- Docker-backed pytest gate with Postgres, Redis, S3, and infrastructure extras:
  1030 passed in 84.58s.
- `git diff --check`: passed.
