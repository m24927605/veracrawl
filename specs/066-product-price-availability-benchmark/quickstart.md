# Quickstart: Product Price Availability Benchmark

## Deterministic Fixture Run

```bash
uv run --python python3.12 --extra dev veracrawl-product-availability-benchmark run \
  tests/fixtures/us-top-ecommerce-product-availability \
  --profile target \
  --out .veracrawl-real-runs/us-top-ecommerce-product-availability
```

## Hosted OpenAI Run

`OPENAI_API_KEY` must be available in the environment or `~/.env`.

```bash
uv run --python python3.12 --extra dev veracrawl-product-availability-benchmark run \
  tests/fixtures/us-top-ecommerce-product-availability \
  --profile target \
  --model-provider openai \
  --openai-model gpt-5.4-mini \
  --out .veracrawl-real-runs/us-top-ecommerce-product-availability-openai
```

Inspect:

```bash
jq . .veracrawl-real-runs/us-top-ecommerce-product-availability-openai/summary.json
jq 'length' .veracrawl-real-runs/us-top-ecommerce-product-availability-openai/model_call_traces.json
jq '[.[] | {site: .site_name, result: .completion_result, price: .price_raw_text, availability: .availability_status, failure_type}]' \
  .veracrawl-real-runs/us-top-ecommerce-product-availability-openai/site_results.json
```

## Browser DOM Source Required Run

This mode requires accepted product field evidence to come from read-only
browser-rendered DOM artifacts while model calls still go through VeraCrawl's
framework-neutral model port.

```bash
uv run --python python3.12 --extra dev --extra browser-playwright \
  veracrawl-product-availability-benchmark run \
  tests/fixtures/us-top-ecommerce-product-availability \
  --profile target \
  --model-provider openai \
  --openai-model gpt-5.4-mini \
  --browser-source-required \
  --out .veracrawl-real-runs/us-top-ecommerce-product-availability-openai-browser-source-required
```

Inspect Amazon DOM evidence:

```bash
jq '.[] | select(.site_name=="Amazon") | {price_raw_text, availability_status, availability_raw_text, artifact_refs, source_observation_refs, model_call_trace_refs}' \
  .veracrawl-real-runs/us-top-ecommerce-product-availability-openai-browser-source-required/site_results.json
jq '.[] | select(.site_name=="Amazon") | {field_name, raw_text, artifact_ref, content_hash_ref, model_call_trace_ref}' \
  .veracrawl-real-runs/us-top-ecommerce-product-availability-openai-browser-source-required/field_evidence.json
```
