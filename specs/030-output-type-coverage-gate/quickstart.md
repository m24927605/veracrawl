# Quickstart: Target Output Type Coverage Gate

```bash
for fixture in \
  output-type-coverage-success \
  output-type-coverage-runtime-unavailable \
  output-type-coverage-missing-output-type \
  output-type-coverage-unsupported-output-type \
  output-type-coverage-derived-context-as-evidence \
  output-type-coverage-candidate-as-evidence \
  output-type-coverage-graph-as-evidence \
  output-type-coverage-memory-as-evidence \
  output-type-coverage-agent-reasoning-as-evidence \
  output-type-coverage-temporal-kg-as-evidence \
  output-type-coverage-missing-table-cell-evidence \
  output-type-coverage-missing-file-lifecycle \
  output-type-coverage-missing-dataset-item-evidence \
  output-type-coverage-missing-fact-verification \
  output-type-coverage-missing-replay
do
  uv run --python python3.12 --extra dev veracrawl-output-coverage run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_output_type_coverage_contracts.py \
  tests/contract/test_output_type_coverage_contract_registry.py \
  tests/contract/test_output_type_coverage_import_boundaries.py \
  tests/unit/test_output_type_coverage_gate.py \
  tests/integration/test_output_type_coverage_fixtures.py
```
