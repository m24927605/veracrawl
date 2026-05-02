# Tasks: VeraCrawl Normalize and Extract Plane

**Input**: Design documents from `/specs/006-normalize-extract-plane/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature implements normalization contracts, anchor maps, link provenance, page classification, site model, extraction strategy, candidates, replay validation, fixtures, and import boundaries.

## Phase 1: Setup

- [X] T001 Add `veracrawl-process` console script target in `pyproject.toml`
- [X] T002 [P] Create process CLI module in `src/veracrawl/cli/process.py`
- [X] T003 [P] Extend processing contracts in `src/veracrawl/contracts/processing.py`
- [X] T004 [P] Create normalization pipeline in `src/veracrawl/normalize/pipeline.py`
- [X] T005 [P] Create extraction candidate runtime in `src/veracrawl/extract/candidates.py`
- [X] T006 [P] Create processing replay validation in `src/veracrawl/review_replay/processing.py`
- [X] T007 [P] Create process fixture assertion helpers in `tests/helpers/process_fixture_assertions.py`

## Phase 2: Foundational

- [X] T008 [P] Write process registry tests in `tests/contract/test_process_contract_registry.py`
- [X] T009 [P] Write process contract tests in `tests/contract/test_process_contracts.py`
- [X] T010 [P] Write process import-boundary tests in `tests/contract/test_process_import_boundaries.py`
- [X] T011 [P] Implement normalization/extraction enums in `src/veracrawl/contracts/enums.py`
- [X] T012 Implement contract exports in `src/veracrawl/contracts/__init__.py`
- [X] T013 Extend registry for process contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`

## Phase 3: User Story 1 - Normalize Raw HTML Into Replayable Documents (Priority: P1)

- [X] T014 [P] [US1] Write normalization unit tests in `tests/unit/test_normalization_pipeline.py`
- [X] T015 [P] [US1] Create `process-static-basic` fixture manifests/oracles under `tests/fixtures/process-static-basic/`
- [X] T016 [US1] Implement HTML text normalization, manifest, text anchors, and anchor map in `src/veracrawl/normalize/pipeline.py`
- [X] T017 [US1] Implement process fixture runner success path in `src/veracrawl/cli/process.py`

## Phase 4: User Story 2 - Extract Links With Provenance And Classify Page Types (Priority: P2)

- [X] T018 [P] [US2] Create `process-link-provenance` fixture manifests/oracles under `tests/fixtures/process-link-provenance/`
- [X] T019 [US2] Implement link extraction, link provenance, page type classification, and site model in `src/veracrawl/normalize/pipeline.py`

## Phase 5: User Story 3 - Create Anchored Extraction Candidates (Priority: P3)

- [X] T020 [P] [US3] Write extraction candidate guard tests in `tests/unit/test_extraction_candidate_guards.py`
- [X] T021 [P] [US3] Create `process-anchored-candidate` fixture manifests/oracles under `tests/fixtures/process-anchored-candidate/`
- [X] T022 [US3] Implement extraction strategy and candidate creation in `src/veracrawl/extract/candidates.py`

## Phase 6: Negative Fixtures And Replay

- [X] T023 [P] Create negative process fixtures under `tests/fixtures/process-missing-raw/`, `tests/fixtures/process-empty-content/`, and `tests/fixtures/process-anchor-gap/`
- [X] T024 [P] Write process replay tests in `tests/unit/test_process_replay.py`
- [X] T025 [P] Write process fixture integration tests in `tests/integration/test_process_fixtures.py`
- [X] T026 Implement typed failure handling for missing raw, empty content, and anchor gap in process runtime
- [X] T027 Implement processing replay validation in `src/veracrawl/review_replay/processing.py`

## Phase 7: Docs And Verification

- [X] T028 [P] Update process usage notes in `README.md`
- [X] T029 [P] Update normalize/extract package map and non-completion boundaries in `docs/10-target-implementation-design.md`
- [X] T030 [P] Update process fixtures and gates in `docs/11-target-testing-and-acceptance.md`
- [X] T031 Run `veracrawl-contracts validate --format json`
- [X] T032 Run process success and negative fixture CLI commands from `quickstart.md`
- [X] T033 Run ruff, mypy, and full pytest gate with a 30-second local timing check
- [X] T034 Run Spec Kit consistency checks equivalent to `$speckit-analyze` and record follow-up in this file
- [X] T035 Verify no code, docs, tests, CLI output, or task text claims evidence/publication, graph/memory, export, distributed persistence, or production scale readiness

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/006-normalize-extract-plane`.
- Consistency review: 13 functional requirements, 7 success criteria, and T001-T035 are contiguous and mapped to contracts, tests, fixtures, docs, and verification gates. No clarification markers remain.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: `process-static-basic`, `process-link-provenance`, `process-anchored-candidate`, `process-missing-raw`, `process-empty-content`, and `process-anchor-gap` all passed their declared oracles through `veracrawl-process run`.
- Quality gate: `ruff check src tests`, `mypy src`, and full `pytest` passed; full suite result was `136 passed in 9.54s`.
- Non-completion boundary: README, target implementation design, target testing docs, spec, tasks, code, tests, and CLI output were checked to avoid claims that evidence/publication, graph/memory, export, distributed persistence, production browser rendering, or production scale readiness are complete.
