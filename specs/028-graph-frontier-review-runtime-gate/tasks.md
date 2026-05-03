# Tasks: VeraCrawl Graph-Driven Frontier And Review Runtime Gate

**Input**: Design documents from `specs/028-graph-frontier-review-runtime-gate/`

## Phase 1: Setup

- [x] T001 Run Spec Kit prerequisite check for 028 feature context
- [x] T002 Add `veracrawl-graph-frontier-review` CLI entry point in `pyproject.toml`

## Phase 2: Foundational Contracts

- [x] T003 Extend graph frontier/review enums in `src/veracrawl/contracts/enums.py`
- [x] T004 Add graph frontier/review runtime contracts in `src/veracrawl/contracts/graph.py`
- [x] T005 Export contracts in `src/veracrawl/contracts/__init__.py`
- [x] T006 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T007 Update registry expectations in `tests/contract/test_contract_registry.py`

## Phase 3: Runtime And Success Path

- [x] T008 Add contract tests in `tests/contract/test_graph_frontier_review_contracts.py`
- [x] T009 Add registry tests in `tests/contract/test_graph_frontier_review_contract_registry.py`
- [x] T010 Add fixture assertion helper in `tests/helpers/graph_frontier_review_fixture_assertions.py`
- [x] T011 Implement deterministic runtime gate in `src/veracrawl/graph/frontier_review.py`
- [x] T012 Implement CLI runner in `src/veracrawl/cli/graph_frontier_review.py`
- [x] T013 Add success fixture/oracles
- [x] T014 Add success integration test

## Phase 4: Needs Review And Negative Cases

- [x] T015 Add import-boundary test
- [x] T016 Add runtime-unavailable fixture/oracles
- [x] T017 Add negative fixture/oracles
- [x] T018 Add negative unit tests
- [x] T019 Add negative integration assertions

## Phase 5: Documentation And Acceptance

- [x] T020 Update README and docs/07, docs/09, docs/10, docs/11
- [x] T021 Update `AGENTS.md` active Spec Kit block for 028
- [x] T022 Run registry validation, ruff, mypy, focused tests, CLI fixtures, and full suites
- [x] T023 Record real verification results in this `tasks.md`

## Validation Record

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` -> passed for 028.
- `uv lock` -> passed.
- `uv run --python python3.12 --extra dev ruff check src tests` -> passed.
- `uv run --python python3.12 --extra dev mypy src` -> passed; 191 source files checked.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` -> passed; registry validation ok.
- `uv run --python python3.12 --extra dev pytest tests/contract/test_graph_frontier_review_contracts.py tests/contract/test_graph_frontier_review_contract_registry.py tests/contract/test_graph_frontier_review_import_boundaries.py tests/unit/test_graph_frontier_review_gate.py tests/integration/test_graph_frontier_review_fixtures.py` -> 19 passed.
- 9-fixture `veracrawl-graph-frontier-review run ... --profile target` loop -> passed for success, runtime-unavailable, and 7 negative fixtures.
- `uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration` -> 506 passed, 5 skipped.
- `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/contract tests/unit tests/integration` -> 511 passed.
- `git diff --check` -> passed.
