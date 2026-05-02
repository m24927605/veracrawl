# Tasks: VeraCrawl Export Connectors

**Input**: Design documents from `/specs/013-export-connectors/`

## Phase 1: Implementation

- [X] T001 Add `veracrawl-export` console script target in `pyproject.toml`
- [X] T002 Create export contracts in `src/veracrawl/contracts/export.py`
- [X] T003 Extend export enums in `src/veracrawl/contracts/enums.py`
- [X] T004 Create export target port in `src/veracrawl/ports/export.py`
- [X] T005 Create deterministic export runtime in `src/veracrawl/export/runtime.py`
- [X] T006 Create export replay validation in `src/veracrawl/review_replay/export.py`
- [X] T007 Create export CLI fixture runner in `src/veracrawl/cli/export.py`
- [X] T008 Extend contract exports and registry coverage
- [X] T009 Add export fixtures and fixture assertion helpers
- [X] T010 Add contract, unit, replay, boundary, import, and integration tests
- [X] T011 Update README and docs/07/10/11
- [X] T012 Run prerequisite, registry, CLI fixture, ruff, mypy, and full pytest gates
- [X] T013 Verify no claims of concrete export adapters, production export delivery, distributed persistence, production browser rendering, or production scale readiness

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/013-export-connectors`.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: `export-file-success`, `export-api-success`, `export-correction-withdrawal-success`, `export-missing-receipt`, `duplicate-export-idempotency`, `withdrawal-missing-mapping`, `destination-unsupported-withdrawal`, and `correction-without-withdrawal` all passed their declared oracles through `veracrawl-export run`.
- Quality gate: `ruff check src tests`, `mypy src`, and full `pytest` passed; full suite result was `259 passed in 10.31s`.
- Non-completion boundary: README, data contracts, target implementation design, target testing docs, spec, tasks, code, tests, and CLI output were checked to avoid claiming completed concrete export adapters, production export delivery, distributed persistence, production browser rendering, or production scale readiness.
