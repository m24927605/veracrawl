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
