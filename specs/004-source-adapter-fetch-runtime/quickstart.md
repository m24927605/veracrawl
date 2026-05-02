# Quickstart: Source Adapter and Fetch Runtime

This quickstart validates deterministic source acquisition. It does not claim production HTTP/browser crawling, production persistence, graph/memory intelligence, export capability, or production scale readiness.

## Validate Registry And Contracts

```bash
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev pytest tests/contract/test_source_acquisition_contract_registry.py
uv run --python python3.12 --extra dev pytest tests/contract/test_source_adapter_runtime_contracts.py
uv run --python python3.12 --extra dev pytest tests/contract/test_source_adapter_import_boundaries.py
```

## Run Success Fixtures

```bash
for fixture in \
  source-http-success \
  source-sitemap-success \
  source-rss-success \
  source-api-success \
  source-document-success
do
  uv run --python python3.12 --extra dev veracrawl-source run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

## Run Negative Fixtures

```bash
for fixture in \
  source-blocked \
  source-rate-limited \
  source-adapter-mismatch \
  source-malformed-response \
  source-retry-exhausted \
  source-missing-artifact
do
  uv run --python python3.12 --extra dev veracrawl-source run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

## Run Full Source Adapter Gate

```bash
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration
```
