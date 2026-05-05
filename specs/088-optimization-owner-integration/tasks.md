# Tasks: Optimization Owner-Service Integration Roadmap

**Input**: Design documents from `specs/088-optimization-owner-integration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required for this VeraCrawl non-trivial platform integration.

## Phase 1: Setup

- [x] T001 Update roadmap references for specs 088-096 in `docs/08-build-roadmap.md`, `specs/038-production-runtime-closure/spec.md`, `specs/080-crawler-intelligence-optimization-roadmap/spec.md`, and `AGENTS.md`
- [x] T002 Add owner-service integration contracts in `src/veracrawl/contracts/crawler_optimization.py`
- [x] T003 Register owner-service integration contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`

## Phase 2: Foundational

- [x] T004 Add replay helper for owner-service integration refs in `src/veracrawl/review_replay/crawler_optimization_owner_integration.py`
- [x] T005 Add import-boundary tests for owner-service integration modules in `tests/contract/test_crawler_optimization_owner_integration_import_boundaries.py`
- [x] T006 Add contract tests for owner-service integration models in `tests/contract/test_crawler_optimization_owner_integration_contracts.py`
- [x] T007 Add registry tests for owner-service integration commands/events/fixtures in `tests/contract/test_crawler_optimization_owner_integration_registry.py`

## Phase 3: User Story 1 - Scheduler Consumes Optimization Decisions

- [x] T008 [US1] Implement scheduler optimization integration in `src/veracrawl/scheduler/optimization_integration.py`
- [x] T009 [US1] Add scheduler integration tests for enqueue/block/retire/stop outcomes in `tests/unit/test_crawler_optimization_owner_integration.py`

## Phase 4: User Story 2 - Processing Owners Consume DOM And Extraction Context

- [x] T010 [US2] Implement normalize optimization integration in `src/veracrawl/normalize/optimization_integration.py`
- [x] T011 [US2] Implement extract/verify optimization integration in `src/veracrawl/extract/optimization_integration.py`
- [x] T012 [US2] Add DOM/extraction integration tests for anchors, LLM-only rejection, and abstention in `tests/unit/test_crawler_optimization_owner_integration.py`

## Phase 5: User Story 3 - Publication Uses Dedupe And Ranking

- [x] T013 [US3] Implement dedupe/identity optimization integration in `src/veracrawl/graph/optimization_integration.py`
- [x] T014 [US3] Implement ranking/publication optimization integration in `src/veracrawl/publish/optimization_integration.py`
- [x] T015 [US3] Add dedupe/ranking integration tests for duplicate suppression, variant retention, and verification-status preservation in `tests/unit/test_crawler_optimization_owner_integration.py`

## Phase 6: User Story 4 - Ops Gates Cost, Recovery, And Regression Evidence

- [x] T016 [US4] Implement cost/cache/budget, drift/recovery, and regression release integration in `src/veracrawl/ops/optimization_integration.py`
- [x] T017 [US4] Add ops integration tests for stale cache, budget overrun, unsafe recovery, missing lower refs, and pass gate in `tests/unit/test_crawler_optimization_owner_integration.py`
- [x] T018 [US4] Add replay gap tests for owner-service integration in `tests/unit/test_crawler_optimization_owner_integration_replay.py`

## Phase 7: Polish And Validation

- [x] T019 Run Spec Kit analyze over `specs/088-optimization-owner-integration/spec.md`, `plan.md`, and `tasks.md`
- [x] T020 Run targeted owner-service integration pytest suite
- [x] T021 Run `uv run --extra dev ruff check`
- [x] T022 Run `uv run --extra dev mypy` on owner-service integration modules and crawler optimization contracts
- [x] T023 Run full `uv run --extra dev pytest`
- [x] T024 Run `git diff --check`
- [x] T025 Record implementation closure and validation results in `specs/088-optimization-owner-integration/spec.md` and this `tasks.md`

## Phase 8: Spec 096 Release Evidence Hardening

- [x] T026 [US4] Extend `OptimizationRegressionReleaseGate` with required/present lower integration kinds, failed lower refs, replay gaps, and metric regression refs in `src/veracrawl/contracts/crawler_optimization.py`
- [x] T027 [US4] Add typed lower-report aggregation in `src/veracrawl/ops/optimization_integration.py` so passing gates are built from 089-095 integration records, not arbitrary string refs
- [x] T028 [US4] Extend replay validation in `src/veracrawl/review_replay/crawler_optimization_owner_integration.py` to fail on missing lower kinds, failed lower reports, replay gaps, and metric regressions
- [x] T029 [US4] Add release-gate hardening tests proving actual lower reports pass, raw string-only lower refs fail, and forged lower-kind coverage without structured report refs fails
- [x] T030 [US4] Record Spec 096 hardening closure in `specs/096-optimization-regression-release-gate/spec.md`

## Dependencies & Execution Order

- Phase 1 must complete before code integration.
- Phase 2 tests and replay helper must exist before story implementation.
- US1 is the MVP and can be validated independently.
- US2 depends on foundational contracts and can run after US1 or in parallel if files do not overlap.
- US3 depends on dedupe/ranking runtime outputs and should run after US1/US2 tests define shared fixtures.
- US4 depends on lower integration refs from US1-US3.
- Phase 7 closes validation and records proof.

## MVP Scope

US1 is the MVP: scheduler integration consumes optimization frontier decisions
with typed enqueue/block/retire/stop outcomes and replay refs.

## Validation

- Spec Kit analyze prerequisite check:
  `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- Targeted tests:
  `uv run --extra dev pytest tests/contract/test_crawler_optimization_owner_integration_contracts.py tests/contract/test_crawler_optimization_owner_integration_registry.py tests/contract/test_crawler_optimization_owner_integration_import_boundaries.py tests/unit/test_crawler_optimization_owner_integration.py tests/unit/test_crawler_optimization_owner_integration_replay.py`
  passed with 16 tests after Spec 096 release evidence hardening.
- Lint:
  `uv run --extra dev ruff check`
- Type check:
  `uv run --extra dev mypy src/veracrawl/scheduler/optimization_integration.py src/veracrawl/normalize/optimization_integration.py src/veracrawl/extract/optimization_integration.py src/veracrawl/graph/optimization_integration.py src/veracrawl/publish/optimization_integration.py src/veracrawl/ops/optimization_integration.py src/veracrawl/review_replay/crawler_optimization_owner_integration.py src/veracrawl/contracts/crawler_optimization.py`
- Full regression:
  `uv run --extra dev pytest`
  passed with 1404 passed, 5 skipped after Spec 096 hardening.
- Diff check:
  `git diff --check`
