# Tasks: VeraCrawl Production Persistence And Queue Runtime

**Input**: Design documents from `/specs/015-production-persistence-queue-runtime/`

## Phase 1: Implementation

- [x] T001 Add `veracrawl-persistence` console script target in `pyproject.toml`
- [x] T002 Create persistence contracts in `src/veracrawl/contracts/persistence.py`
- [x] T003 Extend persistence enums in `src/veracrawl/contracts/enums.py`
- [x] T004 Create persistence ports in `src/veracrawl/ports/persistence.py`
- [x] T005 Create filesystem reference persistence store in `src/veracrawl/runtime_support/persistence_store.py`
- [x] T006 Create persistence runtime in `src/veracrawl/persistence/runtime.py`
- [x] T007 Create persistence replay validation in `src/veracrawl/review_replay/persistence.py`
- [x] T008 Create persistence CLI fixture runner in `src/veracrawl/cli/persistence.py`
- [x] T009 Extend contract exports and registry coverage
- [x] T010 Add persistence fixtures and fixture assertion helpers
- [x] T011 Add contract, unit, replay, boundary, import, and integration tests
- [x] T012 Update README, AGENTS, docs/07, docs/10, and docs/11
- [x] T013 Run prerequisite, registry, CLI fixture, ruff, mypy, and full pytest gates
- [x] T014 Verify no claims of concrete database/queue/cloud adapters, production deployment, production worker fleet, or production observability completion

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/015-production-persistence-queue-runtime`.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: all nine persistence fixtures passed through `veracrawl-persistence run`.
- Quality gate: `uv run --python python3.12 --extra dev ruff check src tests`, `uv run --python python3.12 --extra dev mypy src`, and `uv run --python python3.12 --extra dev pytest tests` passed; full pytest result was `294 passed in 12.07s`.
- Non-completion boundary: README, data contracts, target implementation design, target testing docs, spec, tasks, code, tests, and CLI output avoid claiming completed concrete database/queue/cloud adapters, production deployment, production worker fleet, or production observability completion.
