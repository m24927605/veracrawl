# Tasks: VeraCrawl Multi-Agent Repair

**Input**: Design documents from `/specs/011-multi-agent-repair/`

## Phase 1: Implementation

- [X] T001 Add `veracrawl-agent-workflow` console script target in `pyproject.toml`
- [X] T002 Create multi-agent CLI module in `src/veracrawl/cli/agents.py`
- [X] T003 Extend agent contracts in `src/veracrawl/contracts/agent.py`
- [X] T004 Create orchestration runtime in `src/veracrawl/agents/orchestration.py`
- [X] T005 Create replay validation in `src/veracrawl/review_replay/agents.py`
- [X] T006 Extend registry and contract exports
- [X] T007 Add fixtures and fixture assertion helpers
- [X] T008 Add contract, unit, replay, boundary, import, and integration tests
- [X] T009 Update README and docs/07/10/11
- [X] T010 Run registry, CLI fixture, ruff, mypy, and full pytest gates
- [X] T011 Verify no claims of production agent framework integration, UI, export, distributed persistence, production browser rendering, or production scale readiness

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/011-multi-agent-repair`.
- Consistency review: 11 functional requirements and T001-T011 are mapped to contracts, tests, fixtures, docs, and verification gates. No clarification markers remain.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: `multi-agent-repair-success`, `coordination-arbitration-success`, `repair-loop-evidence-success`, `owner-service-bypass`, `unresolved-coordination-conflict`, and `agent-reasoning-as-evidence` all passed their declared oracles through `veracrawl-agent-workflow run`.
- Quality gate: `ruff check src tests`, `mypy src`, and full `pytest` passed; full suite result was `220 passed in 10.31s`.
- Non-completion boundary: README, data contracts, target implementation design, target testing docs, spec, tasks, code, tests, and CLI output were checked to avoid claiming completed concrete agent framework integration, model SDK integration, review UI, export, distributed persistence, production browser rendering, or production scale readiness.
