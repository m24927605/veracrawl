# Tasks: VeraCrawl Source Adapter and Fetch Runtime

**Input**: Design documents from `/specs/004-source-adapter-fetch-runtime/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature implements source acquisition contracts, deterministic adapters, policy gates, raw artifact preservation, scheduler-to-source runtime flow, replay recovery, fixtures, and import boundaries.

## Phase 1: Setup

- [X] T001 Add `veracrawl-source` console script target in `pyproject.toml`
- [X] T002 [P] Create source CLI module in `src/veracrawl/cli/source.py`
- [X] T003 [P] Create fetch contract module in `src/veracrawl/contracts/fetch.py`
- [X] T004 [P] Create source runtime contract module in `src/veracrawl/contracts/source_runtime.py`
- [X] T005 [P] Create source acquisition runtime module in `src/veracrawl/fetch/acquisition.py`
- [X] T006 [P] Create deterministic source adapter module in `src/veracrawl/adapters/sources/deterministic.py`
- [X] T007 [P] Create source replay validation module in `src/veracrawl/review_replay/source.py`
- [X] T008 [P] Create source fixture assertion helpers in `tests/helpers/source_fixture_assertions.py`

## Phase 2: Foundational

- [X] T009 [P] Write source acquisition registry tests in `tests/contract/test_source_acquisition_contract_registry.py`
- [X] T010 [P] Write source adapter runtime contract tests in `tests/contract/test_source_adapter_runtime_contracts.py`
- [X] T011 [P] Write source import-boundary tests in `tests/contract/test_source_adapter_import_boundaries.py`
- [X] T012 [P] Implement source lifecycle enums in `src/veracrawl/contracts/enums.py`
- [X] T013 [P] Implement FetchAttempt, FetchResult, PageSnapshot, and DocumentArtifact in `src/veracrawl/contracts/fetch.py`
- [X] T014 [P] Implement RateLimitDecision, SourceFailureReport, SourceAcquisitionReport, and SourceFixtureManifest in `src/veracrawl/contracts/source_runtime.py`
- [X] T015 Extend contract exports in `src/veracrawl/contracts/__init__.py`
- [X] T016 Extend registry for source contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`

## Phase 3: User Story 1 - Execute Generic Source Adapters (Priority: P1)

- [X] T017 [P] [US1] Write deterministic source adapter conformance tests in `tests/contract/test_source_adapter_runtime_contracts.py`
- [X] T018 [P] [US1] Write source acquisition success integration tests in `tests/integration/test_source_acquisition_runtime.py`
- [X] T019 [P] [US1] Create success fixture manifests/oracles for HTTP, sitemap, RSS, API-like, and document-source under `tests/fixtures/source-http-success/`, `tests/fixtures/source-sitemap-success/`, `tests/fixtures/source-rss-success/`, `tests/fixtures/source-api-success/`, and `tests/fixtures/source-document-success/`
- [X] T020 [US1] Implement deterministic source adapters for HTTP, sitemap, RSS, API-like, and document-source in `src/veracrawl/adapters/sources/deterministic.py`
- [X] T021 [US1] Implement scheduler frontier and lease to source adapter command flow in `src/veracrawl/fetch/acquisition.py`
- [X] T022 [US1] Implement raw artifact preservation and source acquisition reports in `src/veracrawl/fetch/acquisition.py`
- [X] T023 [US1] Implement success fixture runner paths in `src/veracrawl/cli/source.py`

## Phase 4: User Story 2 - Enforce Source Policy And Retry Gates (Priority: P2)

- [X] T024 [P] [US2] Write source policy and retry unit tests in `tests/unit/test_source_policy_and_retry_gates.py`
- [X] T025 [P] [US2] Create blocked, rate-limited, adapter-mismatch, malformed-response, and retry-exhausted fixture manifests/oracles under `tests/fixtures/source-blocked/`, `tests/fixtures/source-rate-limited/`, `tests/fixtures/source-adapter-mismatch/`, `tests/fixtures/source-malformed-response/`, and `tests/fixtures/source-retry-exhausted/`
- [X] T026 [US2] Implement source policy gate handling in `src/veracrawl/fetch/acquisition.py`
- [X] T027 [US2] Implement rate limit, retry-after, malformed response, and retry-exhausted handling in `src/veracrawl/fetch/acquisition.py`
- [X] T028 [US2] Implement adapter mismatch validation in `src/veracrawl/fetch/acquisition.py`
- [X] T029 [US2] Extend source fixture runner for negative policy/retry scenarios in `src/veracrawl/cli/source.py`

## Phase 5: User Story 3 - Preserve Raw Artifacts And Replay Lineage (Priority: P3)

- [X] T030 [P] [US3] Write source replay recovery unit tests in `tests/unit/test_source_replay_recovery.py`
- [X] T031 [P] [US3] Write negative source fixture integration tests in `tests/integration/test_source_negative_fixtures.py`
- [X] T032 [P] [US3] Create missing-artifact fixture manifest/oracles under `tests/fixtures/source-missing-artifact/`
- [X] T033 [US3] Implement source replay recovery validation in `src/veracrawl/review_replay/source.py`
- [X] T034 [US3] Extend source acquisition runtime to include durable command, event, outbox, policy, lease, and artifact refs in `src/veracrawl/fetch/acquisition.py`
- [X] T035 [US3] Extend source fixture runner for missing-artifact replay failure in `src/veracrawl/cli/source.py`

## Phase 6: User Story 4 - Keep Adapter Runtime Replaceable (Priority: P4)

- [X] T036 [P] [US4] Extend source import-boundary tests for no concrete browser/storage/queue/model/agent dependencies in `tests/contract/test_source_adapter_import_boundaries.py`
- [X] T037 [US4] Keep deterministic adapters under `src/veracrawl/adapters/sources/deterministic.py` and core runtime dependent only on `SourceAdapterPort`, contracts, ports, policy, scheduler, and replay

## Phase 7: Polish And Verification

- [X] T038 [P] Update source adapter usage notes in `README.md`
- [X] T039 [P] Update source acquisition package map and non-completion boundaries in `docs/10-target-implementation-design.md`
- [X] T040 [P] Update source fixtures and gates in `docs/11-target-testing-and-acceptance.md`
- [X] T041 Run `veracrawl-contracts validate --format json`
- [X] T042 Run source success and negative fixture CLI commands from `specs/004-source-adapter-fetch-runtime/quickstart.md`
- [X] T043 Run ruff, mypy, and pytest full source-adapter gate with a 30-second local timing check
- [X] T044 Run Spec Kit consistency checks equivalent to `$speckit-analyze` and record follow-up in this file
- [X] T045 Verify no code, docs, tests, CLI output, or task text claims full production crawler, full browser, production persistence, graph/memory, export, or production scale readiness

## Implementation Verification Record

- Prerequisite check passed for `specs/004-source-adapter-fetch-runtime` with
  `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`,
  `quickstart.md`, and this `tasks.md` present.
- Spec Kit consistency review passed: 15 functional requirements, 8 success
  criteria, contiguous tasks `T001` through `T045`, no blocking markers, and
  source contracts/adapters/fixtures/replay/import-boundary coverage present.
- `veracrawl-contracts validate --format json` passed.
- Source fixture CLI acceptance passed for HTTP, sitemap, RSS, API-like,
  document-source, blocked, rate-limited, adapter-mismatch, malformed-response,
  retry-exhausted, and missing-artifact fixtures.
- Local quality gate passed within 30 seconds: ruff, mypy, and full pytest.
- Non-completion boundary checked: this slice does not claim full production
  crawler, production browser runtime, production persistence, graph/memory,
  export, or production scale readiness.
