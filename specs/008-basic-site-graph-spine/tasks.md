# Tasks: VeraCrawl Basic Site Graph Spine

**Input**: Design documents from `/specs/008-basic-site-graph-spine/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature implements basic graph contracts, deterministic graph build, edge provenance, projection watermark, replay validation, fixtures, and import boundaries.

## Phase 1: Setup

- [X] T001 Add `veracrawl-graph` console script target in `pyproject.toml`
- [X] T002 [P] Create graph CLI module in `src/veracrawl/cli/graph.py`
- [X] T003 [P] Create graph contracts in `src/veracrawl/contracts/graph.py`
- [X] T004 [P] Create graph build runtime in `src/veracrawl/graph/build.py`
- [X] T005 [P] Create graph replay validation in `src/veracrawl/review_replay/graph.py`
- [X] T006 [P] Create graph fixture assertion helpers in `tests/helpers/graph_fixture_assertions.py`

## Phase 2: Foundational

- [X] T007 [P] Write graph registry tests in `tests/contract/test_graph_contract_registry.py`
- [X] T008 [P] Write graph contract tests in `tests/contract/test_graph_contracts.py`
- [X] T009 [P] Write graph import-boundary tests in `tests/contract/test_graph_import_boundaries.py`
- [X] T010 [P] Implement graph enums in `src/veracrawl/contracts/enums.py`
- [X] T011 Implement contract exports in `src/veracrawl/contracts/__init__.py`
- [X] T012 Extend registry for graph contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`

## Phase 3: User Story 1 - Build URL And Hyperlink Graph (Priority: P1)

- [X] T013 [P] [US1] Write graph build unit tests in `tests/unit/test_graph_build.py`
- [X] T014 [P] [US1] Create `graph-url-hyperlink` fixture manifests/oracles under `tests/fixtures/graph-url-hyperlink/`
- [X] T015 [US1] Implement URL node, hyperlink edge, provenance, manifest, and watermark build path in `src/veracrawl/graph/build.py`
- [X] T016 [US1] Implement fixture runner URL/hyperlink success path in `src/veracrawl/cli/graph.py`

## Phase 4: User Story 2 - Build Canonical, Redirect, And Page Structure Edges (Priority: P2)

- [X] T017 [P] [US2] Create `graph-canonical-redirect` and `graph-page-structure` fixtures under `tests/fixtures/`
- [X] T018 [US2] Implement canonical, redirect, page type, and page-structure graph records in `src/veracrawl/graph/build.py`

## Phase 5: User Story 3 - Validate Graph Replay And Evidence Boundary (Priority: P3)

- [X] T019 [P] [US3] Write graph replay tests in `tests/unit/test_graph_replay.py`
- [X] T020 [P] [US3] Write graph evidence-boundary tests in `tests/unit/test_graph_evidence_boundary.py`
- [X] T021 [P] [US3] Create negative graph fixtures under `tests/fixtures/graph-missing-input/`, `tests/fixtures/graph-rebuild-mismatch/`, and `tests/fixtures/graph-as-evidence/`
- [X] T022 [US3] Implement typed failure handling for missing input, rebuild mismatch, and graph-as-evidence boundary violation
- [X] T023 [US3] Implement graph replay validation in `src/veracrawl/review_replay/graph.py`

## Phase 6: Docs And Verification

- [X] T024 [P] Update graph usage notes in `README.md`
- [X] T025 [P] Update graph package map and non-completion boundaries in `docs/10-target-implementation-design.md`
- [X] T026 [P] Update graph fixtures and gates in `docs/11-target-testing-and-acceptance.md`
- [X] T027 Run `veracrawl-contracts validate --format json`
- [X] T028 Run graph success and negative fixture CLI commands from `quickstart.md`
- [X] T029 Run ruff, mypy, and full pytest gate with a 30-second local timing check
- [X] T030 Run Spec Kit consistency checks equivalent to `$speckit-analyze` and record follow-up in this file
- [X] T031 Verify no code, docs, tests, CLI output, or task text claims advanced graph, memory, export, distributed persistence, production browser rendering, or production scale readiness

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/008-basic-site-graph-spine`.
- Consistency review: 13 functional requirements, 7 success criteria, and T001-T031 are contiguous and mapped to contracts, tests, fixtures, docs, and verification gates. No clarification markers remain.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: `graph-url-hyperlink`, `graph-canonical-redirect`, `graph-page-structure`, `graph-missing-input`, `graph-rebuild-mismatch`, and `graph-as-evidence` all passed their declared oracles through `veracrawl-graph run`.
- Quality gate: `ruff check src tests`, `mypy src`, and full `pytest` passed; full suite result was `167 passed in 9.73s`.
- Non-completion boundary: README, target implementation design, target testing docs, spec, tasks, code, tests, and CLI output were checked to avoid claiming completed advanced graph intelligence, memory, export, distributed persistence, production browser rendering, or production scale readiness.
