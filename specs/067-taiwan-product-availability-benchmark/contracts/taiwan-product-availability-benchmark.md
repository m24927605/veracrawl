# Contract: Taiwan Product Availability Benchmark

## CLI

```bash
veracrawl-product-availability-benchmark run \
  tests/fixtures/taiwan-top-ecommerce-product-availability \
  --profile target \
  --out .veracrawl-real-runs/taiwan-top-ecommerce-product-availability
```

Hosted model validation:

```bash
veracrawl-product-availability-benchmark run \
  tests/fixtures/taiwan-top-ecommerce-product-availability \
  --profile target \
  --model-provider openai \
  --openai-model gpt-5.4-mini \
  --out .veracrawl-real-runs/taiwan-top-ecommerce-product-availability-openai
```

## Expected Output Contract

The run MUST write:

- `run_report.json`
- `site_results.json`
- `field_evidence.json`
- `model_call_traces.json`
- `agent_action_traces.json`
- `tool_call_traces.json`
- `context_bundle_traces.json`
- `summary.json`
- state store JSON documents

## Pass/Needs-Review Semantics

- momo and PChome 24h are expected to pass when current public pages expose
  product identity, price, and availability.
- Shopee Taiwan is expected to produce `needs_review` if the allowed live HTTP
  path exposes only a JavaScript shell or the product API returns 403.
- Overall report is expected to be `needs_review` when at least one top platform
  is blocked or lacks source-backed product fields.

## Evidence Rules

- Price/availability values must come from source artifacts, never from model
  output.
- Every published field must include source anchors, artifact refs, content hash
  refs, evidence verification refs, command/event/outbox refs, and replay refs.
- Blocked or source-limited targets must not fabricate values.
