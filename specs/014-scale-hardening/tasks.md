# Tasks: VeraCrawl Scale Hardening

**Input**: Design documents from `/specs/014-scale-hardening/`

## Phase 1: Implementation

- [x] T001 Add `veracrawl-scale` console script target in `pyproject.toml`
- [x] T002 Create scale contracts in `src/veracrawl/contracts/scale.py`
- [x] T003 Extend scale enums in `src/veracrawl/contracts/enums.py`
- [x] T004 Create scale ports in `src/veracrawl/ports/scale.py`
- [x] T005 Create deterministic scale runtime in `src/veracrawl/scale/hardening.py`
- [x] T006 Create scale replay validation in `src/veracrawl/review_replay/scale.py`
- [x] T007 Create scale CLI fixture runner in `src/veracrawl/cli/scale.py`
- [x] T008 Extend contract exports and registry coverage
- [x] T009 Add scale fixtures and fixture assertion helpers
- [x] T010 Add contract, unit, replay, boundary, import, and integration tests
- [x] T011 Update README and docs/07/10/11
- [x] T012 Run prerequisite, registry, CLI fixture, ruff, mypy, and full pytest gates
- [x] T013 Verify no claims of concrete queue/storage/cloud adapters, production distributed persistence, production worker fleet, production browser rendering, or production scale readiness

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/014-scale-hardening`.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: all eight scale fixtures passed through `veracrawl-scale run`.
- Quality gate: `uv run --python python3.12 --extra dev ruff check src tests`, `uv run --python python3.12 --extra dev mypy src`, and `uv run --python python3.12 --extra dev pytest tests` passed; full pytest result was `276 passed in 11.28s`.
- Non-completion boundary: README, data contracts, target implementation design, target testing docs, spec, tasks, code, tests, and CLI output avoid claiming completed concrete queue/storage/cloud adapters, production distributed persistence, production worker fleet, production browser rendering, or production scale readiness.
