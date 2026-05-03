# Tasks: Top Ecommerce Live AI Benchmark

## Phase 1: Spec Kit Setup

- [x] T001 Create `065-top-ecommerce-live-ai-benchmark` feature branch and
  activate the feature context.
- [x] T002 Add 065 spec, research, data model, contract, quickstart, plan, and
  tasks artifacts.
- [x] T003 Amend `AGENTS.md`, `README.md`, `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`, and
  `docs/11-target-testing-and-acceptance.md`.

## Phase 2: Fixtures And Registry

- [x] T004 Add `tests/fixtures/top-ecommerce-public-corpus` manifest and
  oracles.
- [x] T005 Add `tests/fixtures/top-ecommerce-ai-agent-corpus` manifest and
  oracles.
- [x] T006 Register both fixtures in `src/veracrawl/contracts/registry.py`.
- [x] T007 Update contract and integration tests for both fixtures.

## Phase 3: Live Experiments

- [x] T008 Run live preflight/benchmark for the top ecommerce public corpus.
- [x] T009 Run deterministic local AI benchmark for the top ecommerce AI corpus.
- [x] T010 Run hosted OpenAI AI benchmark for the top ecommerce AI corpus.
- [x] T011 Inspect and record model/agent/tool/context/candidate trace counts.

## Phase 4: Validation

- [x] T012 Run Spec Kit prerequisite check.
- [x] T013 Run ruff.
- [x] T014 Run mypy.
- [x] T015 Run registry validation.
- [x] T016 Run focused 065 tests.
- [x] T017 Run full pytest.
- [x] T018 Run Docker-backed pytest.
- [x] T019 Run `git diff --check`.
- [x] T020 Record all validation outputs in this file.
- [x] T021 Commit and fast-forward merge 065.

## Validation Results

- Live public ecommerce corpus:
  `uv run --python python3.12 --extra dev veracrawl-real-benchmark run tests/fixtures/top-ecommerce-public-corpus --profile target --out .veracrawl-real-runs/top-ecommerce-public-corpus`
  passed with `completion_result=pass`, `operator_status=real_world_benchmark_completed`,
  `site_count=6`, `artifact_count=6`, and `replay_bundle_count=6`.
- Live public site observations passed:
  `tw-shopee-home` status `200`, `text/html`, body `158338` bytes, matched refs `4`;
  `tw-momo-home` status `200`, `text/html`, body `60847` bytes, matched refs `5`;
  `tw-pchome-home` status `200`, `text/html`, body `1848` bytes, matched refs `5`;
  `us-amazon-home` status `200`, `text/html`, body `805626` bytes, matched refs `5`;
  `us-walmart-home` status `200`, `text/html`, body `400421` bytes, matched refs `5`;
  `us-ebay-home` status `200`, `text/html`, body `600918` bytes, matched refs `5`.
- Deterministic local AI benchmark:
  `uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run tests/fixtures/top-ecommerce-ai-agent-corpus --profile target --out .veracrawl-real-runs/top-ecommerce-ai-agent-corpus`
  passed with `site_count=6`, `decision_trace_count=24`,
  `model_call_trace_count=24`, `agent_action_trace_count=24`,
  `tool_call_trace_count=24`, `context_bundle_trace_count=24`,
  `extraction_candidate_count=6`, provider `Local model runtime`, and framework
  `VeraCrawl Native Runtime`.
- Hosted OpenAI AI benchmark:
  `uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run tests/fixtures/top-ecommerce-ai-agent-corpus --profile target --model-provider openai --openai-model gpt-5.4-mini --out .veracrawl-real-runs/top-ecommerce-ai-agent-corpus-openai`
  passed with `site_count=6`, `decision_trace_count=24`,
  `model_call_trace_count=24`, `agent_action_trace_count=24`,
  `tool_call_trace_count=24`, `context_bundle_trace_count=24`,
  `extraction_candidate_count=6`, provider `OpenAI Responses API`, and
  framework `VeraCrawl Native Runtime`.
- Hosted OpenAI trace inspection passed:
  `model_call_traces=24`, `agent_action_traces=24`, `tool_call_traces=24`,
  `context_bundle_traces=24`, and `extraction_candidates=6`. First
  `ModelCallTrace` recorded provider `OpenAI Responses API`, model
  `gpt-5.4-mini`, token usage `input_tokens=374`, `output_tokens=256`,
  `total_tokens=630`, `raw_prompt_persisted=false`, and
  `raw_response_persisted=false`.
- Hosted OpenAI extraction candidate inspection passed: all 6 candidates include
  source anchor refs, one artifact ref, one content hash ref, evidence packet
  ref, publication gate ref, and `completion_result=pass`.
- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  completed successfully for `065-top-ecommerce-live-ai-benchmark`.
- `uv run --python python3.12 --extra dev ruff check .` passed.
- `uv run --python python3.12 --extra dev mypy src tests` passed with no
  issues across 670 source files.
- Registry validation passed:
  `uv run --python python3.12 --extra dev python -c 'from veracrawl.contracts.registry import validate_registry; print(validate_registry().model_dump_json(indent=2))'`
  reported `ok=true`, no errors, and no warnings.
- Focused 065 tests passed:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_real_world_benchmark_contract_registry.py tests/contract/test_real_world_ai_agent_contract_registry.py tests/integration/test_real_world_benchmark_fixtures.py tests/integration/test_real_world_ai_agent_fixtures.py tests/unit/test_real_world_benchmark_runtime.py tests/unit/test_real_world_ai_agent_runtime.py tests/unit/test_real_world_ai_agent_replay.py`
  reported `19 passed in 1.08s`.
- Full pytest passed:
  `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  reported `1256 passed, 5 skipped in 241.00s`.
- Docker-backed pytest passed:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  reported `1261 passed in 273.26s`.
- `git diff --check` passed.
