# Tasks: VeraCrawl Review Replay Ops Console

**Input**: Design documents from `/specs/012-review-replay-ops/`

## Phase 1: Implementation

- [X] T001 Add `veracrawl-ops` console script target in `pyproject.toml`
- [X] T002 Create ops contracts in `src/veracrawl/contracts/ops.py`
- [X] T003 Extend ops/review/replay enums in `src/veracrawl/contracts/enums.py`
- [X] T004 Create deterministic ops console runtime in `src/veracrawl/ops/console.py`
- [X] T005 Create ops replay validation in `src/veracrawl/review_replay/ops.py`
- [X] T006 Create ops CLI fixture runner in `src/veracrawl/cli/ops.py`
- [X] T007 Extend contract exports and registry coverage
- [X] T008 Add ops fixtures and fixture assertion helpers
- [X] T009 Add contract, unit, replay, boundary, import, and integration tests
- [X] T010 Update README and docs/07/10/11
- [X] T011 Run prerequisite, registry, CLI fixture, ruff, mypy, and full pytest gates
- [X] T012 Verify no claims of production UI, production monitoring backend, export delivery, distributed persistence, production browser rendering, or production scale readiness

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/012-review-replay-ops`.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: `review-console-success`, `replay-audit-success`, `quality-dashboard-success`, `missing-review-evidence`, `unresolved-failure-without-recovery`, `stale-dashboard-projection`, and `unsafe-recovery-without-review` all passed their declared oracles through `veracrawl-ops run`.
- Quality gate: `ruff check src tests`, `mypy src`, and full `pytest` passed; full suite result was `240 passed in 10.56s`.
- Non-completion boundary: README, data contracts, target implementation design, target testing docs, spec, tasks, code, tests, and CLI output were checked to avoid claiming completed production UI, production observability backend, export delivery, distributed persistence, production browser rendering, or production scale readiness.
