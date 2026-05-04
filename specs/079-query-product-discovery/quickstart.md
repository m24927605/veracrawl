# Quickstart: Query Product Discovery And Offer Ranking

Run the deterministic query discovery fixture:

```sh
uv run --python python3.12 --extra dev veracrawl-product-discovery run \
  tests/fixtures/query-product-discovery-success \
  --profile target \
  --out .veracrawl-test-runs/query-product-discovery-success
```

Run the no-candidates negative fixture:

```sh
uv run --python python3.12 --extra dev veracrawl-product-discovery run \
  tests/fixtures/query-product-discovery-no-candidates \
  --profile target \
  --out .veracrawl-test-runs/query-product-discovery-no-candidates
```

Run a live Taiwan query with hosted OpenAI model traces:

```sh
set -a; source ~/.env; set +a
uv run --python python3.12 --extra dev veracrawl-product-discovery run \
  tests/fixtures/taiwan-iphone17-query-product-discovery \
  --profile target \
  --model-provider openai \
  --openai-model gpt-5.4-mini \
  --out .veracrawl-real-runs/taiwan-iphone17-query-product-discovery-openai
```

Inspect:

```sh
jq . .veracrawl-real-runs/taiwan-iphone17-query-product-discovery-openai/discovery_report.json
jq . .veracrawl-real-runs/taiwan-iphone17-query-product-discovery-openai/ranked_offers.json
```

The input fixture must contain only query/search entry pages. Product URLs must
appear only in `discovered_candidates.json` and the derived
`derived_product_availability_manifest.json`.
