# Tasks: VeraCrawl Browser and Network Acquisition Runtime

**Input**: Design documents from `/specs/005-browser-network-acquisition/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature implements real local HTTP acquisition, network/browser contracts, browser sandbox gates, fixture/oracle validation, security negative fixtures, replay validation, registry coverage, and import boundaries.

## Phase 1: Setup

- [X] T001 Add `veracrawl-network` console script target in `pyproject.toml`
- [X] T002 [P] Create network CLI module in `src/veracrawl/cli/network.py`
- [X] T003 [P] Create network contract module in `src/veracrawl/contracts/network.py`
- [X] T004 [P] Create browser contract module in `src/veracrawl/contracts/browser.py`
- [X] T005 [P] Create network port module in `src/veracrawl/ports/network.py`
- [X] T006 [P] Create browser port module in `src/veracrawl/ports/browser.py`
- [X] T007 [P] Create network acquisition runtime in `src/veracrawl/fetch/network_acquisition.py`
- [X] T008 [P] Create browser observation runtime in `src/veracrawl/browser/observation.py`
- [X] T009 [P] Create network/browser replay validation in `src/veracrawl/review_replay/network_browser.py`
- [X] T010 [P] Create fixture helpers in `tests/helpers/benchmark_server.py` and `tests/helpers/network_fixture_assertions.py`

## Phase 2: Foundational

- [X] T011 [P] Write registry tests in `tests/contract/test_network_browser_contract_registry.py`
- [X] T012 [P] Write network/browser contract tests in `tests/contract/test_network_browser_contracts.py`
- [X] T013 [P] Write import-boundary tests in `tests/contract/test_network_browser_import_boundaries.py`
- [X] T014 [P] Implement network/browser lifecycle enums in `src/veracrawl/contracts/enums.py`
- [X] T015 [P] Implement NetworkRequest, NetworkResponse, RedirectHop, and NetworkAcquisitionReport in `src/veracrawl/contracts/network.py`
- [X] T016 [P] Implement BrowserSandboxPolicy and BrowserInteractionStep in `src/veracrawl/contracts/browser.py`
- [X] T017 [P] Implement NetworkClientPort and BrowserObservationPort protocols
- [X] T018 Extend contract exports in `src/veracrawl/contracts/__init__.py`
- [X] T019 Extend registry for network/browser contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`

## Phase 3: User Story 1 - Acquire Real HTTP Sources Through Port (Priority: P1)

- [X] T020 [P] [US1] Write HTTP success integration tests in `tests/integration/test_network_acquisition_runtime.py`
- [X] T021 [P] [US1] Create `network-http-success` and `network-http-redirect` fixture manifests/oracles under `tests/fixtures/`
- [X] T022 [US1] Implement standard-library HTTP adapter in `src/veracrawl/adapters/network/stdlib_http.py`
- [X] T023 [US1] Implement local benchmark server helper in `tests/helpers/benchmark_server.py`
- [X] T024 [US1] Implement network acquisition runtime request/response/redirect flow in `src/veracrawl/fetch/network_acquisition.py`
- [X] T025 [US1] Implement success fixture runner paths in `src/veracrawl/cli/network.py`

## Phase 4: User Story 2 - Enforce Network Policy Gates (Priority: P2)

- [X] T026 [P] [US2] Write network policy gate unit tests in `tests/unit/test_network_policy_gates.py`
- [X] T027 [P] [US2] Create negative network fixture manifests/oracles for robots, private-network, egress, rate, size, redirect, and timeout under `tests/fixtures/`
- [X] T028 [US2] Implement egress/private-network/robots/rate/size/redirect/timeout gates in `src/veracrawl/fetch/network_acquisition.py`
- [X] T029 [US2] Extend network fixture runner for negative network scenarios in `src/veracrawl/cli/network.py`

## Phase 5: User Story 3 - Record Browser Observation Contracts And Sandbox Gates (Priority: P3)

- [X] T030 [P] [US3] Write browser sandbox unit tests in `tests/unit/test_browser_sandbox_gates.py`
- [X] T031 [P] [US3] Create `network-browser-readonly` and `network-browser-unsafe-side-effect` fixture manifests/oracles under `tests/fixtures/`
- [X] T032 [US3] Implement deterministic browser observation adapter in `src/veracrawl/adapters/browser/deterministic.py`
- [X] T033 [US3] Implement browser observation runtime and sandbox gate in `src/veracrawl/browser/observation.py`
- [X] T034 [US3] Extend network CLI runner for browser fixtures in `src/veracrawl/cli/network.py`

## Phase 6: User Story 4 - Preserve Replaceable Adapter Boundaries (Priority: P4)

- [X] T035 [P] [US4] Extend import-boundary tests for no concrete HTTP/browser/storage/queue/model/agent dependencies in core packages
- [X] T036 [US4] Keep concrete network and browser adapters under `src/veracrawl/adapters/` and core dependent only on contracts, ports, policy, scheduler, durable, and replay

## Phase 7: Replay, Docs, And Verification

- [X] T037 [P] Write network/browser replay unit tests in `tests/unit/test_network_browser_replay.py`
- [X] T038 [P] Write negative fixture integration tests in `tests/integration/test_network_browser_negative_fixtures.py`
- [X] T039 Implement replay validation in `src/veracrawl/review_replay/network_browser.py`
- [X] T040 Update network/browser usage notes in `README.md`
- [X] T041 Update network/browser package map and non-completion boundaries in `docs/10-target-implementation-design.md`
- [X] T042 Update network/browser fixtures and gates in `docs/11-target-testing-and-acceptance.md`
- [X] T043 Run `veracrawl-contracts validate --format json`
- [X] T044 Run success and negative fixture CLI commands from `quickstart.md`
- [X] T045 Run ruff, mypy, and full pytest gate with a 30-second local timing check
- [X] T046 Run Spec Kit consistency checks equivalent to `$speckit-analyze` and record follow-up in this file
- [X] T047 Verify no code, docs, tests, CLI output, or task text claims full browser rendering, authenticated crawling, graph/memory, export, distributed persistence, or production scale readiness

## Implementation Verification Record

- Prerequisite check passed for `specs/005-browser-network-acquisition` with
  `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`,
  `quickstart.md`, and this `tasks.md` present.
- Spec Kit consistency review passed: 14 functional requirements, 7 success
  criteria, contiguous tasks `T001` through `T047`, no blocking markers, and
  network/browser contracts, adapters, fixtures, replay, security, and
  import-boundary coverage present.
- `veracrawl-contracts validate --format json` passed.
- Network/browser fixture CLI acceptance passed for HTTP success, HTTP redirect,
  browser read-only, robots blocked, private-network denied, egress denied, rate
  budget, size budget, redirect denied, timeout, and unsafe browser side-effect
  fixtures.
- Local quality gate passed within 30 seconds: ruff, mypy, and full pytest
  (`120 passed`).
- Non-completion boundary checked: this slice does not claim full JavaScript
  rendering, authenticated crawling, graph/memory, export, distributed
  persistence, or production scale readiness.
