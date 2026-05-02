# Quickstart: Model Provider Adapter Operational Gate

Run focused checks:

```sh
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_model_provider_adapter_contracts.py \
  tests/contract/test_model_provider_adapter_contract_registry.py \
  tests/contract/test_model_provider_adapter_import_boundaries.py \
  tests/unit/test_model_provider_adapter_gate.py \
  tests/integration/test_model_provider_adapter_fixtures.py
```

Run deterministic fixtures:

```sh
for fixture in \
  model-provider-adapter-success \
  model-provider-adapter-runtime-unavailable \
  model-provider-adapter-raw-prompt-leak \
  model-provider-adapter-raw-response-leak \
  model-provider-adapter-provider-state-canonical \
  model-provider-adapter-missing-context-trace \
  model-provider-adapter-missing-replay \
  model-provider-adapter-missing-security-privacy \
  model-provider-adapter-unsafe-tool-suggestion \
  model-provider-adapter-unsupported-provider
do
  uv run --python python3.12 --extra dev veracrawl-model-providers run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```
