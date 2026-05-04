# Quickstart: Amazon Official Product API Adapter

Run the shared official API fixture without credentials:

```sh
uv run --python python3.12 --extra dev veracrawl-ecommerce-official-api run-live \
  tests/fixtures/us-ecommerce-official-api-product-availability \
  --profile target \
  --out .veracrawl-test-runs/us-ecommerce-official-api-product-availability
```

Credentialed Amazon run requires:

```sh
export AMAZON_CREATORS_API_ENDPOINT="https://affiliate-program.amazon.com/..."
export AMAZON_CREATORS_API_BEARER_TOKEN="..."
uv run --python python3.12 --extra dev veracrawl-ecommerce-official-api run-live \
  tests/fixtures/us-ecommerce-official-api-product-availability \
  --profile target \
  --out .veracrawl-real-runs/us-ecommerce-official-api-product-availability \
  --require-pass
```

Inspect:

```sh
jq '.site_result_refs, .diagnostics' .veracrawl-test-runs/us-ecommerce-official-api-product-availability/run_report.json
```

