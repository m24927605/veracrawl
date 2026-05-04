# Quickstart: Taiwan Product Availability Benchmark

Run local deterministic validation:

```bash
uv run --python python3.12 --extra dev \
  veracrawl-product-availability-benchmark run \
  tests/fixtures/taiwan-top-ecommerce-product-availability \
  --profile target \
  --out .veracrawl-real-runs/taiwan-top-ecommerce-product-availability
```

Run hosted OpenAI validation:

```bash
uv run --python python3.12 --extra dev \
  veracrawl-product-availability-benchmark run \
  tests/fixtures/taiwan-top-ecommerce-product-availability \
  --profile target \
  --model-provider openai \
  --openai-model gpt-5.4-mini \
  --out .veracrawl-real-runs/taiwan-top-ecommerce-product-availability-openai
```

Inspect site results:

```bash
jq '[.[] | {site_name, result: .completion_result, price: .price_raw_text, availability: .availability_status, failure_type, diagnostics}]' \
  .veracrawl-real-runs/taiwan-top-ecommerce-product-availability-openai/site_results.json
```
