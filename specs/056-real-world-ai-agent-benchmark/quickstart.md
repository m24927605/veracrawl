# Quickstart: Real-World AI Agent Crawl Planning And Extraction Benchmark

Run deterministic focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_real_world_ai_agent_contracts.py \
  tests/contract/test_real_world_ai_agent_contract_registry.py \
  tests/contract/test_real_world_ai_agent_import_boundaries.py \
  tests/unit/test_real_world_ai_agent_runtime.py \
  tests/unit/test_real_world_ai_agent_replay.py \
  tests/integration/test_real_world_ai_agent_fixtures.py
```

Run the live public AI benchmark:

```bash
uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run \
  tests/fixtures/real-world-ai-agent-public-corpus \
  --profile target \
  --out .veracrawl-real-runs/real-world-ai-agent-public-corpus
```

Run the live public AI benchmark with hosted OpenAI model calls:

```bash
set -a; source ~/.env; set +a
uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run \
  tests/fixtures/real-world-ai-agent-public-corpus \
  --profile target \
  --model-provider openai \
  --openai-model gpt-5.4-mini \
  --out .veracrawl-real-runs/real-world-ai-agent-openai-public-corpus
```

Expected success summary:

```json
{
  "ok": true,
  "completion_result": "pass",
  "operator_status": "real_world_ai_agent_benchmark_completed",
  "site_count": 4,
  "decision_trace_count": 16,
  "model_call_trace_count": 16,
  "agent_action_trace_count": 16,
  "tool_call_trace_count": 16,
  "context_bundle_trace_count": 16,
  "extraction_candidate_count": 4
}
```

Inspect proof artifacts:

```bash
ls .veracrawl-real-runs/real-world-ai-agent-public-corpus
```

Required files:

- `run_report.json`
- `decision_traces.json`
- `extraction_candidates.json`
- `model_call_traces.json`
- `agent_action_traces.json`
- `tool_call_traces.json`
- `context_bundle_traces.json`
- `model_requests.json`
- `model_responses.json`
- `agent_run_requests.json`
- `agent_run_results.json`
- `summary.json`
- `real_world/run_report.json`
- `real_world/site_observations.json`

Validation gate:

```bash
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
uv lock
uv run --python python3.12 --extra dev ruff check .
uv run --python python3.12 --extra dev mypy src tests
uv run --python python3.12 --extra dev python -m veracrawl.cli.contracts validate --format json
uv run --python python3.12 --extra dev pytest
VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 \
  uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest
```
