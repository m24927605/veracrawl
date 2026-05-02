# Quickstart: Agent Runtime Adapter Operational Gate

```sh
uv run --python python3.12 --extra dev veracrawl-agent-adapters run \
  tests/fixtures/agent-runtime-adapter-success \
  --profile target \
  --out .veracrawl-test-runs/agent-runtime-adapter-success
```

Run all fixtures:

```sh
for fixture in \
  agent-runtime-adapter-success \
  agent-runtime-adapter-runtime-unavailable \
  agent-runtime-adapter-raw-prompt-leak \
  agent-runtime-adapter-framework-state-canonical \
  agent-runtime-adapter-missing-model-trace \
  agent-runtime-adapter-missing-tool-trace \
  agent-runtime-adapter-missing-replay \
  agent-runtime-adapter-missing-security-privacy \
  agent-runtime-adapter-unsupported-framework
do
  uv run --python python3.12 --extra dev veracrawl-agent-adapters run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Required verification:

```sh
uv run --python python3.12 --extra dev veracrawl-contracts validate
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_agent_runtime_adapter_contracts.py \
  tests/contract/test_agent_runtime_adapter_contract_registry.py \
  tests/contract/test_agent_runtime_adapter_import_boundaries.py \
  tests/unit/test_agent_runtime_adapter_gate.py \
  tests/integration/test_agent_runtime_adapter_fixtures.py
```
