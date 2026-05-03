# Tasks: Multi-Page Deep Crawl Frontier Benchmark

**Input**: Design documents from `/specs/060-multi-page-deep-crawl-frontier-benchmark/`
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/

**Tests**: Contract, registry, import-boundary, unit, integration, replay,
negative fixture, focused, full, Docker-backed, and CLI validation are required
before marking this spec complete.

## Phase 1: Setup

- [x] T001 Activate `060-multi-page-deep-crawl-frontier-benchmark` Spec Kit feature context.
- [x] T002 Add 060 plan, research, data model, contract, quickstart, and tasks artifacts.
- [x] T003 Update `AGENTS.md` active Spec Kit pointer to 060.
- [x] T004 Update `README.md`, `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md` for 060 boundaries and commands.

## Phase 2: Foundational Contracts

- [x] T005 Add deep crawl failure/action/stop enums in `src/veracrawl/contracts/enums.py`.
- [x] T006 Add deep crawl contracts in `src/veracrawl/contracts/deep_crawl.py`.
- [x] T007 Export deep crawl contracts in `src/veracrawl/contracts/__init__.py`.
- [x] T008 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`.
- [x] T009 Add contract tests in `tests/contract/test_deep_crawl_contracts.py`.
- [x] T010 Add registry tests in `tests/contract/test_deep_crawl_contract_registry.py`.
- [x] T011 Add import-boundary tests in `tests/contract/test_deep_crawl_import_boundaries.py`.

## Phase 3: Runtime And Replay

- [x] T012 Implement deep crawl benchmark runtime in `src/veracrawl/benchmarks/deep_crawl.py`.
- [x] T013 Implement replay checks in `src/veracrawl/review_replay/deep_crawl.py`.
- [x] T014 Add runtime tests in `tests/unit/test_deep_crawl_runtime.py`.
- [x] T015 Add replay tests in `tests/unit/test_deep_crawl_replay.py`.

## Phase 4: CLI And Fixtures

- [x] T016 Add `veracrawl-deep-crawl-benchmark` CLI in `src/veracrawl/cli/deep_crawl.py`.
- [x] T017 Register CLI entry point in `pyproject.toml`.
- [x] T018 Add success fixture in `tests/fixtures/deep-crawl-quality-corpus`.
- [x] T019 Add negative fixture `tests/fixtures/deep-crawl-duplicate-loop`.
- [x] T020 Add negative fixture `tests/fixtures/deep-crawl-off-origin-pollution`.
- [x] T021 Add negative fixture `tests/fixtures/deep-crawl-robots-denied`.
- [x] T022 Add negative fixture `tests/fixtures/deep-crawl-budget-exhausted`.
- [x] T023 Add negative fixture `tests/fixtures/deep-crawl-infinite-pagination`.
- [x] T024 Add negative fixture `tests/fixtures/deep-crawl-replay-mismatch`.
- [x] T025 Add integration fixture tests in `tests/integration/test_deep_crawl_fixtures.py`.

## Phase 5: Validation

- [x] T026 Run Spec Kit prerequisite check for 060.
- [x] T027 Run ruff.
- [x] T028 Run mypy.
- [x] T029 Run registry validation.
- [x] T030 Run focused 060 tests.
- [x] T031 Run deterministic deep crawl CLI validation.
- [x] T032 Run full pytest.
- [x] T033 Run Docker-backed pytest.
- [x] T034 Run `git diff --check`.
- [x] T035 Record all validation outputs in this file.
- [x] T036 Verify no docs, code, CLI output, or tests claim field-level oracle, precision/recall, repair success, or production-quality release completion.

## Validation Results

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks
  --include-tasks` passed for
  `specs/060-multi-page-deep-crawl-frontier-benchmark` with `research.md`,
  `data-model.md`, `contracts/`, `quickstart.md`, and `tasks.md` available.
- Initial parallel `uv run ... ruff` collided with a concurrent `uv run ...
  pytest` package reinstall and failed before executing lint
  (`failed to remove ... veracrawl-0.1.0.dist-info`). The gate was rerun
  sequentially.
- `uv run --python python3.12 --extra dev ruff check .`: all checks passed.
- `uv run --python python3.12 --extra dev mypy src tests`: success across 630
  source files.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate
  --format json`: registry validation returned `ok: true`, `errors: []`,
  `warnings: []`; follow-up registry introspection confirmed
  `target_area_count: 64`.
- Focused 060 pytest gate:
  `tests/contract/test_deep_crawl_contracts.py`,
  `tests/contract/test_deep_crawl_contract_registry.py`,
  `tests/contract/test_deep_crawl_import_boundaries.py`,
  `tests/unit/test_deep_crawl_runtime.py`,
  `tests/unit/test_deep_crawl_replay.py`, and
  `tests/integration/test_deep_crawl_fixtures.py` passed with
  `29 passed in 9.83s`.
- Deterministic deep crawl CLI gate:
  `uv run --python python3.12 --extra dev veracrawl-deep-crawl-benchmark run
  tests/fixtures/deep-crawl-quality-corpus --profile quality --out
  .veracrawl-test-runs/deep-crawl-quality-corpus` returned `ok: true`,
  `completion_result: pass`, `operator_status: deep_crawl_completed`,
  `site_count: 5`, `covered_page_count: 50`, `observed_page_count: 50`,
  `frontier_decision_count: 70`, `stop_reason_count: 5`,
  `duplicate_suppressed_count: 5`, and `replay_bundle_count: 125`.
- Full non-Docker pytest gate:
  `uv run --python python3.12 --extra dev pytest` passed with `1132 passed,
  5 skipped in 182.13s`.
- Docker-backed pytest gate:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1
  VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python
  python3.12 --extra dev --extra postgres --extra queue-redis --extra
  object-s3 pytest` passed with `1137 passed in 215.10s`.
- `git diff --check`: passed.
- Boundary check: `rg` confirmed 060-facing docs describe field-level oracle
  extraction, precision/recall, repair success, and final production-quality
  release readiness as separate later gates rather than as completed by 060.
