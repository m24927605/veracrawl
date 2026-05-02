# Tasks: VeraCrawl Memory Kernel

**Input**: Design documents from `/specs/010-memory-kernel/`  
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature implements memory contracts, deterministic memory write/retrieve runtime, invalidation exclusion, cross-scope tunnel policy, evidence boundary failures, fixtures, and import boundaries.

## Phase 1: Setup

- [X] T001 Add `veracrawl-memory` console script target in `pyproject.toml`
- [X] T002 [P] Create memory CLI module in `src/veracrawl/cli/memory.py`
- [X] T003 [P] Create memory contracts in `src/veracrawl/contracts/memory.py`
- [X] T004 [P] Create memory kernel runtime in `src/veracrawl/memory/kernel.py`
- [X] T005 [P] Create memory replay validation in `src/veracrawl/review_replay/memory.py`
- [X] T006 [P] Create memory fixture assertion helpers in `tests/helpers/memory_fixture_assertions.py`

## Phase 2: Foundational

- [X] T007 [P] Write memory registry tests in `tests/contract/test_memory_contract_registry.py`
- [X] T008 [P] Write memory contract tests in `tests/contract/test_memory_contracts.py`
- [X] T009 [P] Write memory import-boundary tests in `tests/contract/test_memory_import_boundaries.py`
- [X] T010 [P] Implement memory enums in `src/veracrawl/contracts/enums.py`
- [X] T011 Implement contract exports in `src/veracrawl/contracts/__init__.py`
- [X] T012 Extend registry for memory contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`

## Phase 3: User Story 1 - Write And Retrieve Scoped Memory

- [X] T013 [P] Write memory kernel unit tests in `tests/unit/test_memory_kernel.py`
- [X] T014 [P] Create `memory-write-retrieve-success` fixture manifests/oracles
- [X] T015 Implement memory event, retrieval trace, operational temporal record, and report success path
- [X] T016 Implement memory fixture runner success path

## Phase 4: User Story 2 - Exclude Invalidated Or Tainted Memory

- [X] T017 [P] Create `memory-invalidation-exclusion` and `poisoned-memory-blocked` fixtures
- [X] T018 Implement invalidation exclusion and tainted prompt-use failure
- [X] T019 [P] Write memory retrieval and replay tests

## Phase 5: User Story 3 - Enforce Cross-Scope And Evidence Boundaries

- [X] T020 [P] Create `cross-scope-sanitized-memory`, `unauthorized-cross-scope-memory`, and `memory-as-evidence` fixtures
- [X] T021 Implement cross-scope tunnel and memory-as-evidence failure handling
- [X] T022 [P] Write cross-scope policy and memory evidence boundary tests
- [X] T023 [P] Write integration fixture tests in `tests/integration/test_memory_fixtures.py`

## Phase 6: Docs And Verification

- [X] T024 [P] Update memory usage notes in `README.md`
- [X] T025 [P] Update memory contracts in `docs/07-data-contracts.md`
- [X] T026 [P] Update memory package map and non-completion boundaries in `docs/10-target-implementation-design.md`
- [X] T027 [P] Update memory fixtures and gates in `docs/11-target-testing-and-acceptance.md`
- [X] T028 Run `veracrawl-contracts validate --format json`
- [X] T029 Run memory fixture CLI commands from `quickstart.md`
- [X] T030 Run ruff, mypy, and full pytest gate with a 30-second local timing check
- [X] T031 Run Spec Kit consistency checks equivalent to `$speckit-analyze` and record follow-up in this file
- [X] T032 Verify no code, docs, tests, CLI output, or task text claims production memory store, vector search, export, distributed persistence, production browser rendering, or production scale readiness

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/010-memory-kernel`.
- Consistency review: 13 functional requirements, 7 success criteria, and T001-T032 are contiguous and mapped to contracts, tests, fixtures, docs, and verification gates. No clarification markers remain.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: `memory-write-retrieve-success`, `memory-invalidation-exclusion`, `cross-scope-sanitized-memory`, `poisoned-memory-blocked`, `unauthorized-cross-scope-memory`, and `memory-as-evidence` all passed their declared oracles through `veracrawl-memory run`.
- Quality gate: `ruff check src tests`, `mypy src`, and full `pytest` passed; full suite result was `204 passed in 10.13s`.
- Non-completion boundary: README, data contracts, target implementation design, target testing docs, spec, tasks, code, tests, and CLI output were checked to avoid claiming completed production memory store, vector search, export, distributed persistence, production browser rendering, or production scale readiness.
