# Quickstart: Dynamic Source Adapter Runtime Foundation

Run focused tests:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_dynamic_source_runtime_contracts.py \
  tests/contract/test_dynamic_source_runtime_contract_registry.py \
  tests/contract/test_dynamic_source_runtime_import_boundaries.py \
  tests/unit/test_dynamic_source_runtime_gate.py \
  tests/integration/test_dynamic_source_runtime_fixtures.py
```

Run fixtures:

```sh
for fixture in \
  dynamic-source-runtime-success \
  dynamic-source-runtime-runtime-unavailable \
  dynamic-source-runtime-raw-secret-leak \
  dynamic-source-runtime-adapter-state-canonical \
  dynamic-source-runtime-missing-credential-audit \
  dynamic-source-runtime-missing-document-artifact \
  dynamic-source-runtime-missing-api-payload \
  dynamic-source-runtime-missing-replay \
  dynamic-source-runtime-unsafe-browser-side-effect \
  dynamic-source-runtime-unsupported-adapter
do
  uv run --python python3.12 --extra dev veracrawl-source-runtime run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```
