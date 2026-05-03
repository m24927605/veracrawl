# Quickstart: Top Ecommerce Live AI Benchmark

## Live Public Corpus

```bash
uv run --python python3.12 --extra dev veracrawl-real-benchmark run \
  tests/fixtures/top-ecommerce-public-corpus \
  --profile target \
  --out .veracrawl-real-runs/top-ecommerce-public-corpus
```

Inspect:

```bash
jq . .veracrawl-real-runs/top-ecommerce-public-corpus/summary.json
```

## Local Deterministic AI Run

```bash
uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run \
  tests/fixtures/top-ecommerce-ai-agent-corpus \
  --profile target \
  --out .veracrawl-real-runs/top-ecommerce-ai-agent-corpus
```

## Hosted OpenAI AI Run

Ensure `OPENAI_API_KEY` exists in the environment or `~/.env`.

```bash
uv run --python python3.12 --extra dev veracrawl-real-ai-benchmark run \
  tests/fixtures/top-ecommerce-ai-agent-corpus \
  --profile target \
  --model-provider openai \
  --out .veracrawl-real-runs/top-ecommerce-ai-agent-corpus-openai
```

Trace checks:

```bash
jq 'length' .veracrawl-real-runs/top-ecommerce-ai-agent-corpus-openai/model_call_traces.json
jq 'length' .veracrawl-real-runs/top-ecommerce-ai-agent-corpus-openai/agent_action_traces.json
jq 'length' .veracrawl-real-runs/top-ecommerce-ai-agent-corpus-openai/tool_call_traces.json
jq 'length' .veracrawl-real-runs/top-ecommerce-ai-agent-corpus-openai/context_bundle_traces.json
jq 'length' .veracrawl-real-runs/top-ecommerce-ai-agent-corpus-openai/extraction_candidates.json
```
