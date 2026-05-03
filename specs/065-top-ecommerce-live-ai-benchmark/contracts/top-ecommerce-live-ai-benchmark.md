# Contract: Top Ecommerce Live AI Benchmark

## CLI Contracts

### Live Public Corpus

```text
veracrawl-real-benchmark run tests/fixtures/top-ecommerce-public-corpus \
  --profile target \
  --out .veracrawl-real-runs/top-ecommerce-public-corpus
```

Expected success summary:

```json
{
  "ok": true,
  "fixture_id": "top-ecommerce-public-corpus",
  "completion_result": "pass",
  "operator_status": "real_world_benchmark_completed",
  "site_count": 6
}
```

### AI Agent Corpus

```text
veracrawl-real-ai-benchmark run tests/fixtures/top-ecommerce-ai-agent-corpus \
  --profile target \
  --model-provider openai \
  --out .veracrawl-real-runs/top-ecommerce-ai-agent-corpus-openai
```

Expected success summary:

```json
{
  "ok": true,
  "fixture_id": "top-ecommerce-ai-agent-corpus",
  "completion_result": "pass",
  "operator_status": "real_world_ai_agent_benchmark_completed",
  "site_count": 6,
  "decision_trace_count": 24,
  "model_call_trace_count": 24,
  "agent_action_trace_count": 24,
  "tool_call_trace_count": 24,
  "context_bundle_trace_count": 24,
  "extraction_candidate_count": 6
}
```

## Fixture Contracts

- `tests/fixtures/top-ecommerce-public-corpus/manifest.yaml` must validate as
  `RealWorldBenchmarkCorpusManifest`.
- `tests/fixtures/top-ecommerce-ai-agent-corpus/manifest.yaml` must validate as
  `RealWorldAIAgentBenchmarkManifest`.
- Both fixtures must be registered in `FIXTURE_ORACLES`.

## Boundary Contracts

- Core must not import site-specific scraper modules, OpenAI SDK modules,
  LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, browser runtimes, or
  anti-bot tooling for this benchmark.
- OpenAI access remains inside the model-provider adapter behind
  `ModelProviderPort`.
- Agent execution remains inside the framework-neutral `AgentRuntimePort`.
- LLM output is advisory only and cannot be source evidence.
