# Tasks: Real-World AI Agent Crawl Planning And Extraction Benchmark

**Input**: Design documents from `/specs/056-real-world-ai-agent-benchmark/`

## Phase 1: Roadmap And Spec Kit Documents

- [x] T001 Amend `specs/038-production-runtime-closure/spec.md` to include 056 as the approved post-055 AI agent public benchmark spec.
- [x] T002 Amend `docs/08-build-roadmap.md` to include 056 and its completion gate.
- [x] T003 Complete Spec Kit `spec.md`, clarification assumptions, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and `tasks.md`.

## Phase 2: Contracts And Registry

- [x] T004 Add real-world AI agent benchmark failure/decision enums in `src/veracrawl/contracts/enums.py`.
- [x] T005 Add real-world AI agent benchmark contracts in `src/veracrawl/contracts/real_world_ai_agent.py`.
- [x] T006 Export real-world AI agent benchmark contracts in `src/veracrawl/contracts/__init__.py`.
- [x] T007 Register contracts, commands, events, fixture oracles, and target area in `src/veracrawl/contracts/registry.py`.
- [x] T008 [P] Add contract tests in `tests/contract/test_real_world_ai_agent_contracts.py`.
- [x] T009 [P] Add registry tests in `tests/contract/test_real_world_ai_agent_contract_registry.py`.
- [x] T010 [P] Add import-boundary tests in `tests/contract/test_real_world_ai_agent_import_boundaries.py`.

## Phase 3: Runtime, Replay, And CLI

- [x] T011 Implement AI benchmark runtime in `src/veracrawl/benchmarks/real_world_ai_agent.py`.
- [x] T012 Implement replay validation in `src/veracrawl/review_replay/real_world_ai_agent.py`.
- [x] T013 Implement CLI in `src/veracrawl/cli/real_ai_benchmark.py`.
- [x] T014 Register CLI entry point in `pyproject.toml`.
- [x] T015 [P] Add runtime unit tests in `tests/unit/test_real_world_ai_agent_runtime.py`.
- [x] T016 [P] Add replay unit tests in `tests/unit/test_real_world_ai_agent_replay.py`.

## Phase 4: Fixtures And Oracles

- [x] T017 Add success public AI benchmark fixture in `tests/fixtures/real-world-ai-agent-public-corpus`.
- [x] T018 Add negative fixtures for missing model trace, missing candidate anchor, LLM output as evidence, publication bypass, framework-native state, and missing replay.
- [x] T019 [P] Add fixture integration tests in `tests/integration/test_real_world_ai_agent_fixtures.py`.

## Phase 5: Docs

- [x] T020 Update `docs/07-data-contracts.md`.
- [x] T021 Update `docs/08-build-roadmap.md`.
- [x] T022 Update `docs/10-target-implementation-design.md`.
- [x] T023 Update `docs/11-target-testing-and-acceptance.md`.
- [x] T024 Update `AGENTS.md` active Spec Kit pointer.
- [x] T025 Update `README.md`.

## Phase 6: Verification

- [x] T026 Run Spec Kit prerequisite check.
- [x] T027 Run `uv lock`.
- [x] T028 Run ruff.
- [x] T029 Run mypy.
- [x] T030 Run registry validation.
- [x] T031 Run focused row 056 tests.
- [x] T032 Run real public AI benchmark CLI gate.
- [x] T033 Run full non-Docker pytest gate.
- [x] T034 Run Docker-backed pytest gate.
- [x] T035 Run `git diff --check`.
- [x] T036 Record validation results.

## Validation Results

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  passed for `specs/056-real-world-ai-agent-benchmark`.
- `uv lock` resolved successfully.
- Initial focused ruff found import/order and line-length issues in the new 056
  slice; fixed and reran.
- `uv run --python python3.12 --extra dev ruff check .`: all checks passed.
- Initial full `mypy src tests` exposed 11 pre-existing test typing gaps outside
  the 056 runtime; fixed the affected tests without changing production
  behavior.
- `uv run --python python3.12 --extra dev mypy src tests`: success across 599
  source/test files.
- `uv run --python python3.12 --extra dev python -m veracrawl.cli.contracts
  validate --format json`: registry validation returned `ok: true`, no errors,
  no warnings.
- Focused row 056 pytest gate:
  `uv run --python python3.12 --extra dev pytest
  tests/contract/test_real_world_ai_agent_contracts.py
  tests/contract/test_real_world_ai_agent_contract_registry.py
  tests/contract/test_real_world_ai_agent_import_boundaries.py
  tests/unit/test_real_world_ai_agent_runtime.py
  tests/unit/test_real_world_ai_agent_replay.py
  tests/integration/test_real_world_ai_agent_fixtures.py`
  returned 17 passed in 0.61s.
- Real public AI benchmark CLI gate:
  `uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run
  tests/fixtures/real-world-ai-agent-public-corpus --profile target --out
  .veracrawl-real-runs/real-world-ai-agent-public-corpus` returned
  `completion_result=pass`,
  `operator_status=real_world_ai_agent_benchmark_completed`, `site_count=4`,
  `decision_trace_count=16`, `model_call_trace_count=16`,
  `agent_action_trace_count=16`, `tool_call_trace_count=16`,
  `context_bundle_trace_count=16`, and `extraction_candidate_count=4`.
- Hosted OpenAI public AI benchmark CLI gate after loading `OPENAI_API_KEY` from
  `~/.env`:
  `uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run
  tests/fixtures/real-world-ai-agent-public-corpus --profile target
  --model-provider openai --openai-model gpt-5.4-mini --out
  .veracrawl-real-runs/real-world-ai-agent-openai-public-corpus` returned
  `completion_result=pass`,
  `operator_status=real_world_ai_agent_benchmark_completed`, `site_count=4`,
  `decision_trace_count=16`, `model_call_trace_count=16`,
  `agent_action_trace_count=16`, `tool_call_trace_count=16`,
  `context_bundle_trace_count=16`, `extraction_candidate_count=4`,
  `verified_provider_names=["OpenAI Responses API"]`,
  `verified_framework_names=["VeraCrawl Native Runtime"]`; recorded model trace
  provider/model proof: `provider_name=OpenAI Responses API`,
  `model_id=gpt-5.4-mini`, `trace_count=16`, sample token usage
  `input_tokens=438`, `output_tokens=187`, `total_tokens=625`.
- Full non-Docker pytest gate after hosted OpenAI adapter addition: 1058 passed,
  5 skipped in 56.42s.
- Docker-backed pytest gate with Postgres, Redis, S3, and infrastructure extras:
  1063 passed in 84.81s.
- `git diff --check`: passed.
