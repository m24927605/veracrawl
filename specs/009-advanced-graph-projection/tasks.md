# Tasks: VeraCrawl Advanced Graph Projection Spine

**Input**: Design documents from `/specs/009-advanced-graph-projection/`  
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature implements advanced graph projection contracts, deterministic projection rebuild, graph signals, temporal graph records, mismatch reports, evidence boundary failures, fixtures, and import boundaries.

## Phase 1: Setup

- [X] T001 Add `veracrawl-projection` console script target in `pyproject.toml`
- [X] T002 [P] Create projection CLI module in `src/veracrawl/cli/projection.py`
- [X] T003 [P] Extend graph/projection contracts in `src/veracrawl/contracts/graph.py`
- [X] T004 [P] Create advanced graph projection runtime in `src/veracrawl/graph/projection.py`
- [X] T005 [P] Extend graph replay validation in `src/veracrawl/review_replay/graph.py`
- [X] T006 [P] Create projection fixture assertion helpers in `tests/helpers/projection_fixture_assertions.py`

## Phase 2: Foundational

- [X] T007 [P] Write advanced graph projection registry tests in `tests/contract/test_advanced_graph_projection_contract_registry.py`
- [X] T008 [P] Write advanced graph projection contract tests in `tests/contract/test_advanced_graph_projection_contracts.py`
- [X] T009 [P] Write import-boundary tests in `tests/contract/test_advanced_graph_projection_import_boundaries.py`
- [X] T010 [P] Implement graph projection enums in `src/veracrawl/contracts/enums.py`
- [X] T011 Implement contract exports in `src/veracrawl/contracts/__init__.py`
- [X] T012 Extend registry for projection contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`

## Phase 3: User Story 1 - Rebuild Advanced Graph Projection

- [X] T013 [P] Write advanced graph projection unit tests in `tests/unit/test_advanced_graph_projection.py`
- [X] T014 [P] Create `projection-rebuild-success` fixture manifests/oracles
- [X] T015 Implement projection spec, rebuild job, watermark, delta, quality, signal, temporal record, and report success path
- [X] T016 Implement projection fixture runner success path

## Phase 4: User Story 2 - Emit Frontier And Review Graph Signals

- [X] T017 [P] Create `graph-signal-frontier-review` fixture manifests/oracles
- [X] T018 Implement frontier/review signal contract generation
- [X] T019 [P] Write graph signal evidence boundary tests in `tests/unit/test_graph_signal_evidence_boundary.py`

## Phase 5: User Story 3 - Prove Temporal Graph Foundation And Negative Replay

- [X] T020 [P] Create `temporal-graph-foundation` fixture manifests/oracles
- [X] T021 [P] Create negative fixtures for missing watermark, projection mismatch, and graph signal as evidence
- [X] T022 Implement typed failure handling for missing watermark, mismatch, and graph-signal-as-evidence boundary violation
- [X] T023 [P] Write advanced graph replay tests in `tests/unit/test_advanced_graph_replay.py`
- [X] T024 [P] Write integration fixture tests in `tests/integration/test_advanced_graph_projection_fixtures.py`

## Phase 6: Docs And Verification

- [X] T025 [P] Update advanced graph usage notes in `README.md`
- [X] T026 [P] Update graph projection contracts in `docs/07-data-contracts.md`
- [X] T027 [P] Update graph projection package map and non-completion boundaries in `docs/10-target-implementation-design.md`
- [X] T028 [P] Update advanced graph fixtures and gates in `docs/11-target-testing-and-acceptance.md`
- [X] T029 Run `veracrawl-contracts validate --format json`
- [X] T030 Run advanced graph projection fixture CLI commands from `quickstart.md`
- [X] T031 Run ruff, mypy, and full pytest gate with a 30-second local timing check
- [X] T032 Run Spec Kit consistency checks equivalent to `$speckit-analyze` and record follow-up in this file
- [X] T033 Verify no code, docs, tests, CLI output, or task text claims memory, export, distributed persistence, production browser rendering, production graph store operations, or production scale readiness

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/009-advanced-graph-projection`.
- Consistency review: 14 functional requirements, 7 success criteria, and T001-T033 are contiguous and mapped to contracts, tests, fixtures, docs, and verification gates. No clarification markers remain.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: `projection-rebuild-success`, `graph-signal-frontier-review`, `temporal-graph-foundation`, `projection-missing-watermark`, `projection-mismatch`, and `graph-signal-as-evidence` all passed their declared oracles through `veracrawl-projection run`.
- Quality gate: `ruff check src tests`, `mypy src`, and full `pytest` passed; full suite result was `185 passed in 10.06s`.
- Non-completion boundary: README, data contracts, target implementation design, target testing docs, spec, tasks, code, tests, and CLI output were checked to avoid claiming completed memory, export, distributed persistence, production browser rendering, production graph store operations, or production scale readiness.
