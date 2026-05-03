# Quickstart: Source Coverage Adapter Operational Gate

```sh
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_source_coverage_contracts.py \
  tests/contract/test_source_coverage_contract_registry.py \
  tests/contract/test_source_coverage_import_boundaries.py \
  tests/unit/test_source_coverage_gate.py \
  tests/integration/test_source_coverage_fixtures.py
```

```sh
for fixture in \
  source-coverage-adapter-success \
  source-coverage-adapter-runtime-unavailable \
  source-coverage-adapter-native-state-canonical \
  source-coverage-adapter-raw-secret-leak \
  source-coverage-adapter-missing-browser-refs \
  source-coverage-adapter-missing-credential-audit \
  source-coverage-adapter-missing-document-artifact \
  source-coverage-adapter-missing-api-payload \
  source-coverage-adapter-missing-replay \
  source-coverage-adapter-unsafe-browser-side-effect \
  source-coverage-adapter-unsupported-adapter
do
  uv run --python python3.12 --extra dev veracrawl-source-coverage run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```
