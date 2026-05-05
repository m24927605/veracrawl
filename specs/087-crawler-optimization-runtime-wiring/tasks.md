# Tasks: Crawler Optimization Runtime Wiring

**Feature**: 087 crawler optimization runtime wiring  
**Branch**: `087-crawler-optimization-runtime-wiring`

## Phase 1: Setup

- [x] T001 Update `.specify/feature.json` and Spec Kit artifacts for spec 087.
- [x] T002 Add runtime wiring data contracts in `src/veracrawl/contracts/crawler_optimization.py`.

## Phase 2: Foundational

- [x] T003 Register runtime wiring contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`.
- [x] T004 Add runtime replay helper in `src/veracrawl/review_replay/crawler_optimization_runtime.py`.
- [x] T005 Add import-boundary tests for runtime wiring.

## Phase 3: User Story 1 - Runtime Uses Optimization Scores

- [x] T006 [P] [US1] Add frontier runtime wiring contract tests in `tests/contract/test_crawler_optimization_runtime_wiring_contracts.py`.
- [x] T007 [US1] Implement runtime frontier scoring service in `src/veracrawl/optimization/runtime.py`.
- [x] T008 [US1] Add unit tests for allowed and policy-blocked URL decisions in `tests/unit/test_crawler_optimization_runtime_wiring.py`.

## Phase 4: User Story 2 - Runtime Produces DOM And Extraction Context

- [x] T009 [US2] Implement DOM/extraction context service in `src/veracrawl/optimization/runtime.py`.
- [x] T010 [US2] Add unit tests for DOM context, extractor attempts, confidence, and LLM-as-evidence rejection in `tests/unit/test_crawler_optimization_runtime_wiring.py`.

## Phase 5: User Story 3 - Runtime Applies Dedupe And Ranking

- [x] T011 [US3] Implement dedupe/ranking service in `src/veracrawl/optimization/runtime.py`.
- [x] T012 [US3] Add unit tests for duplicate suppression, variant preservation, and ranking refs in `tests/unit/test_crawler_optimization_runtime_wiring.py`.

## Phase 6: User Story 4 - Ops Aggregates Metrics

- [x] T013 [US4] Implement runtime optimization aggregate service in `src/veracrawl/optimization/runtime.py`.
- [x] T014 [US4] Add replay tests in `tests/unit/test_crawler_optimization_runtime_wiring_replay.py`.
- [x] T015 [US4] Add registry tests in `tests/contract/test_crawler_optimization_runtime_wiring_registry.py`.

## Phase 7: Verification

- [x] T016 Run targeted pytest, ruff, mypy, full pytest, and `git diff --check`.

## Validation

- `uv run --extra dev pytest tests/contract/test_crawler_optimization_runtime_wiring_contracts.py tests/contract/test_crawler_optimization_runtime_wiring_registry.py tests/contract/test_crawler_optimization_runtime_wiring_import_boundaries.py tests/unit/test_crawler_optimization_runtime_wiring.py tests/unit/test_crawler_optimization_runtime_wiring_replay.py`
- `uv run --extra dev ruff check`
- `uv run --extra dev mypy src/veracrawl/optimization/runtime.py src/veracrawl/review_replay/crawler_optimization_runtime.py src/veracrawl/contracts/crawler_optimization.py`
- `uv run --extra dev pytest`
- `git diff --check`
