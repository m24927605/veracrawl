# Tasks: Multi-Agent Orchestration And Repair Runtime

**Input**: Design documents from `/specs/050-multi-agent-orchestration-repair-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Extend multi-agent failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Extend multi-agent repair report contract in `src/veracrawl/contracts/agent.py`
- [x] T003 Register row 050 fixtures and target coverage in `src/veracrawl/contracts/registry.py`
- [x] T004 [P] Update contract tests in `tests/contract/test_multi_agent_contracts.py`
- [x] T005 [P] Update registry tests in `tests/contract/test_multi_agent_contract_registry.py`

## Phase 2: Runtime And CLI

- [x] T006 Update orchestration runtime in `src/veracrawl/agents/orchestration.py`
- [x] T007 Update replay validation in `src/veracrawl/review_replay/agents.py`
- [x] T008 Update CLI run report in `src/veracrawl/cli/agents.py`
- [x] T009 [P] Update orchestration unit tests in `tests/unit/test_multi_agent_orchestration.py`
- [x] T010 [P] Update repair boundary unit tests in `tests/unit/test_multi_agent_repair_boundary.py`
- [x] T011 [P] Update replay unit tests in `tests/unit/test_multi_agent_replay.py`
- [x] T012 [P] Update integration tests in `tests/integration/test_multi_agent_fixtures.py`

## Phase 3: Fixtures

- [x] T013 [P] Add crawl repair success fixture
- [x] T014 [P] Add extraction repair success fixture
- [x] T015 [P] Add missing agent/model runtime fixture
- [x] T016 [P] Add missing live evidence fixture
- [x] T017 [P] Add missing tool gate fixture
- [x] T018 [P] Add missing owner command fixture
- [x] T019 [P] Add replay mismatch fixture
- [x] T020 [P] Update existing multi-agent fixture oracles

## Phase 4: Docs

- [x] T021 [P] Update `README.md`
- [x] T022 [P] Update `docs/07-data-contracts.md`
- [x] T023 [P] Update `docs/08-build-roadmap.md`
- [x] T024 [P] Update `docs/10-target-implementation-design.md`
- [x] T025 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T026 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T027 Run Spec Kit prerequisite check
- [x] T028 Run `uv lock`
- [x] T029 Run ruff
- [x] T030 Run mypy
- [x] T031 Run registry validation
- [x] T032 Run focused row 050 tests
- [x] T033 Run row 050 CLI fixture loop
- [x] T034 Run full non-Docker pytest gate
- [x] T035 Run Docker-backed pytest gate
- [x] T036 Run `git diff --check`
- [x] T037 Record validation results

## Validation Results

- Spec Kit prerequisite: passed for `specs/050-multi-agent-orchestration-repair-runtime`.
- `uv lock`: resolved 30 packages.
- `ruff check .`: passed.
- Focused mypy: passed for `src`, row 050 contract/unit/integration tests, and registry tests; 247 source files checked.
- Registry validation: `ok=true`, no errors.
- Focused pytest: 25 passed.
- `veracrawl-agent-workflow` CLI loop: 13 fixtures passed.
- Full non-Docker pytest: 950 passed, 5 skipped.
- Docker-backed pytest: 955 passed.
- `git diff --check`: passed.
