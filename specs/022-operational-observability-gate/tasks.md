# Tasks: VeraCrawl Operational Observability Gate

**Input**: Design documents from `specs/022-operational-observability-gate/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Phase 1: Setup

- [x] T001 Run Spec Kit prerequisite check for 022 feature context
- [x] T002 Add `veracrawl-observability` CLI entry point in `pyproject.toml`

## Phase 2: Foundational Contracts

- [x] T003 Extend observability enums and failure/action mappings in `src/veracrawl/contracts/enums.py`
- [x] T004 Extend ops contracts with `ObservabilitySignal`, `MetricSample`, `TraceSpan`, `AlertRecord`, `RunbookAction`, `ObservabilityReport`, and `ObservabilityFixtureManifest` in `src/veracrawl/contracts/ops.py`
- [x] T005 Export new observability contracts in `src/veracrawl/contracts/__init__.py`
- [x] T006 Register observability contracts, commands, events, fixture oracles, and target area in `src/veracrawl/contracts/registry.py`
- [x] T007 Update registry expectations in `tests/contract/test_contract_registry.py`

## Phase 3: User Story 1 - Verify Operational Visibility (P1)

**Independent Test**: `observability-success` passes only when canonical metrics, traces, alerts, runbooks, dashboard watermarks, cost/quality, failure/recovery, DR, redaction, backend/collector handoff, policy, command/event/outbox, and replay refs are present.

- [x] T008 [P] [US1] Add observability contract tests in `tests/contract/test_operational_observability_contracts.py`
- [x] T009 [P] [US1] Add observability registry tests in `tests/contract/test_operational_observability_contract_registry.py`
- [x] T010 [P] [US1] Add success fixture assertion helper in `tests/helpers/observability_fixture_assertions.py`
- [x] T011 [US1] Implement core observability success gate in `src/veracrawl/runtime_support/observability.py`
- [x] T012 [US1] Implement backend-neutral CLI runner in `src/veracrawl/cli/observability.py`
- [x] T013 [US1] Add `observability-success` fixture/oracles under `tests/fixtures/observability-success/`
- [x] T014 [US1] Add observability success fixture integration test in `tests/integration/test_operational_observability_fixtures.py`

## Phase 4: User Story 2 - Reject Fake Observability Completion (P2)

**Independent Test**: no-runtime and data-surface-only paths return `needs_review` and cannot claim operational observability pass.

- [x] T015 [P] [US2] Add observability import-boundary test in `tests/contract/test_operational_observability_import_boundaries.py`
- [x] T016 [P] [US2] Add no-runtime and data-surface-only fixture/oracles under `tests/fixtures/`
- [x] T017 [US2] Implement no-runtime/contract-only/data-surface-only observability result behavior in `src/veracrawl/runtime_support/observability.py`
- [x] T018 [US2] Add CLI no-runtime and data-surface-only coverage in `tests/integration/test_operational_observability_fixtures.py`

## Phase 5: User Story 3 - Surface Missing Signals And Runbook Failures (P3)

**Independent Test**: every negative observability fixture fails deterministically with missing refs, typed failures, recovery actions, policy refs, redaction status, and replay status.

- [x] T019 [P] [US3] Add negative fixture/oracles for missing metrics, traces, alerts, runbook, dashboard watermark, DR refs, redaction, replay, secret leak, and unsafe runbook under `tests/fixtures/`
- [x] T020 [P] [US3] Add negative unit tests in `tests/unit/test_operational_observability_gate.py`
- [x] T021 [US3] Implement negative observability failure scenarios and recovery action generation in `src/veracrawl/runtime_support/observability.py`
- [x] T022 [US3] Add negative fixture integration assertions in `tests/integration/test_operational_observability_fixtures.py`

## Phase 6: Documentation And Acceptance

- [x] T023 Update `README.md` with operational observability gate usage and non-completion boundary
- [x] T024 Update `docs/07-data-contracts.md` with operational observability gate contracts, commands, events, fixture rules, and target state
- [x] T025 Update `docs/09-target-capability-model.md` with operational observability acceptance language
- [x] T026 Update `docs/10-target-implementation-design.md` with the operational observability gate slice
- [x] T027 Update `docs/11-target-testing-and-acceptance.md` with observability fixture contract and acceptance gates
- [x] T028 Update `AGENTS.md` active Spec Kit block for 022
- [x] T029 Run registry validation, ruff, mypy, focused tests, CLI no-runtime/negative fixtures, and full test suite
- [x] T030 Record real verification results in this `tasks.md`

## Dependencies

- Phase 1 must complete before contract or implementation work.
- Phase 2 blocks all user stories.
- US1 establishes the success path and canonical pass semantics.
- US2 depends on shared contracts and can run after US1 contracts exist.
- US3 depends on the observability gate core and can run after US1 success behavior exists.
- Documentation and acceptance run after implementation and tests.

## Parallel Examples

- T008, T009, and T010 can run in parallel after T003-T007.
- T015 and T016 can run in parallel after foundational contracts.
- T019 and T020 can run in parallel after the negative scenario names are fixed.

## Validation Record

- Spec Kit prerequisite check: `.specify/scripts/bash/check-prerequisites.sh --json --include-tasks` returned feature dir `specs/022-operational-observability-gate` and available docs `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md`.
- Contract registry validation: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-contracts validate --format json` returned `"ok": true`.
- Focused observability tests: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/contract/test_operational_observability_contracts.py tests/contract/test_operational_observability_contract_registry.py tests/contract/test_operational_observability_import_boundaries.py tests/unit/test_operational_observability_gate.py tests/integration/test_operational_observability_fixtures.py` returned `17 passed in 0.43s`.
- CLI success/no-runtime/data-surface-only/negative fixtures: `veracrawl-observability run` returned `pass` for `observability-success`, `needs_review` for `observability-runtime-unavailable` and `observability-data-surface-only`, and `fail` for all ten negative fixtures with expected operator statuses.
- Ruff: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 ruff check src tests` returned `All checks passed!`.
- Mypy: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 mypy src` returned `Success: no issues found in 169 source files`.
- Lockfile refresh: `uv lock` returned `Resolved 30 packages`.
- Full pytest without Docker live env: `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests` returned `400 passed, 5 skipped in 13.10s`.
- Docker-backed full pytest: `VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests` returned `402 passed, 3 skipped in 34.63s`.
