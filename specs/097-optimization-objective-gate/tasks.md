# Tasks: Optimization Objective Gate

**Input**: Design documents from `specs/097-optimization-objective-gate/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required for this VeraCrawl non-trivial platform integration.

## Phase 1: Setup

- [x] T001 Update roadmap references for spec 097 in `AGENTS.md`, `docs/08-build-roadmap.md`, `specs/038-production-runtime-closure/spec.md`, `specs/068-production-grade-crawler-closure-roadmap/spec.md`, and `specs/080-crawler-intelligence-optimization-roadmap/spec.md`
- [x] T002 Add objective gate contracts in `src/veracrawl/contracts/crawler_optimization.py`
- [x] T003 Register objective gate contracts, commands, events, fixtures, and target-area coverage in `src/veracrawl/contracts/registry.py`

## Phase 2: Foundational

- [x] T004 Add replay helper for objective gate refs in `src/veracrawl/review_replay/crawler_optimization_objective_gate.py`
- [x] T005 Add import-boundary tests in `tests/contract/test_crawler_optimization_objective_gate_import_boundaries.py`
- [x] T006 Add contract tests in `tests/contract/test_crawler_optimization_objective_gate_contracts.py`
- [x] T007 Add registry tests in `tests/contract/test_crawler_optimization_objective_gate_registry.py`

## Phase 3: User Story 1 - Objective Score Is Computable And Replayable

- [x] T008 [US1] Implement objective score formula and report builder in `src/veracrawl/optimization/objective_gate.py`
- [x] T009 [US1] Add score formula, threshold, missing refs, low score, and formula mismatch tests in `tests/unit/test_crawler_optimization_objective_gate.py`
- [x] T010 [US1] Add replay gap tests for objective score reports in `tests/unit/test_crawler_optimization_objective_gate_replay.py`

## Phase 4: User Story 2 - Agent Decision Loop Is Bounded And Evidence-Backed

- [x] T011 [US2] Implement agent decision-loop evidence builder in `src/veracrawl/optimization/objective_gate.py`
- [x] T012 [US2] Add observe/think/act/verify, confidence, stop condition, deterministic refs, LLM fallback, and LLM-output-as-evidence tests in `tests/unit/test_crawler_optimization_objective_gate.py`
- [x] T013 [US2] Add replay gap tests for agent decision-loop evidence in `tests/unit/test_crawler_optimization_objective_gate_replay.py`

## Phase 5: User Story 3 - Release Gate Aggregates Objective, Agent, And Lower Optimization Evidence

- [x] T014 [US3] Implement objective release gate aggregation in `src/veracrawl/optimization/objective_gate.py`
- [x] T015 [US3] Add lower gate, objective score, agent loop, policy, replay, and pass/fail aggregation tests in `tests/unit/test_crawler_optimization_objective_gate.py`
- [x] T016 [US3] Add replay gap tests for objective release gates in `tests/unit/test_crawler_optimization_objective_gate_replay.py`

## Phase 6: Polish And Validation

- [x] T017 Run Spec Kit analyze over `specs/097-optimization-objective-gate/spec.md`, `plan.md`, and `tasks.md`
- [x] T018 Run targeted objective gate pytest suite
- [x] T019 Run `uv run --extra dev ruff check`
- [x] T020 Run `uv run --extra dev mypy` on objective gate modules, registry, and contracts
- [x] T021 Run full `uv run --extra dev pytest`
- [x] T022 Run `git diff --check`
- [x] T023 Record implementation closure and validation results in `specs/097-optimization-objective-gate/spec.md` and this `tasks.md`
- [x] T024 Perform objective completion audit against the user prompt and record concrete evidence before local commit

## Dependencies & Execution Order

- Phase 1 must complete before runtime implementation.
- Phase 2 tests and replay helper must exist before story implementation.
- US1 is the MVP because release and agent gates depend on score reports.
- US2 can run after shared contracts exist and is independently testable.
- US3 depends on US1 and US2 pass evidence plus existing 096 lower gate reports.
- Phase 6 closes validation and records proof.

## MVP Scope

US1 is the MVP: deterministic objective score computation and replayable score
reports prove whether an optimization slice meets the approved formula and
threshold.

## Validation

- Spec Kit analyze prerequisite check:
  `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- Targeted tests:
  `uv run --extra dev pytest tests/contract/test_crawler_optimization_objective_gate_contracts.py tests/contract/test_crawler_optimization_objective_gate_registry.py tests/contract/test_crawler_optimization_objective_gate_import_boundaries.py tests/unit/test_crawler_optimization_objective_gate.py tests/unit/test_crawler_optimization_objective_gate_replay.py`
  passed with 21 tests.
- Lint:
  `uv run --extra dev ruff check`
  passed.
- Type check:
  `uv run --extra dev mypy src/veracrawl/optimization/objective_gate.py src/veracrawl/review_replay/crawler_optimization_objective_gate.py src/veracrawl/contracts/crawler_optimization.py src/veracrawl/contracts/registry.py`
  passed with no issues.
- Full regression:
  `uv run --extra dev pytest`
  passed with 1425 passed, 5 skipped.
- Diff check:
  `git diff --check`
  passed.
