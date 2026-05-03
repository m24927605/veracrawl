# Quickstart: Real Agent And Model Adapter Runtime

Run one success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-agent-model-runtime run \
  tests/fixtures/agent-model-adapter-local-runtime-success \
  --profile target \
  --out .veracrawl-test-runs/agent-model-adapter-local-runtime-success
```

Run the complete row 049 fixture loop:

```bash
tmpdir=$(mktemp -d)
for fixture in tests/fixtures/agent-model-adapter-*; do
  uv run --python python3.12 --extra dev veracrawl-agent-model-runtime run \
    "$fixture" \
    --profile target \
    --out "$tmpdir/$(basename "$fixture")"
done
```

Run focused validation:

```bash
uv run --python python3.12 --extra dev ruff check .
uv run --python python3.12 --extra dev mypy src \
  tests/contract/test_agent_model_adapter_runtime_contracts.py \
  tests/contract/test_agent_model_adapter_runtime_import_boundaries.py \
  tests/unit/test_agent_model_adapter_runtime.py \
  tests/unit/test_agent_model_adapter_runtime_adapters.py \
  tests/integration/test_agent_model_adapter_runtime_fixtures.py \
  tests/contract/test_contract_registry.py
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_agent_model_adapter_runtime_contracts.py \
  tests/contract/test_agent_model_adapter_runtime_import_boundaries.py \
  tests/unit/test_agent_model_adapter_runtime.py \
  tests/unit/test_agent_model_adapter_runtime_adapters.py \
  tests/integration/test_agent_model_adapter_runtime_fixtures.py
uv run --python python3.12 --extra dev python -m veracrawl.cli.contracts validate --format json
```
