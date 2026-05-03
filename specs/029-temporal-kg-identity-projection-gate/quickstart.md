# Quickstart: Temporal KG Identity Projection Gate

Run the deterministic fixture gate:

```bash
for fixture in \
  temporal-kg-projection-success \
  temporal-kg-false-merge-adjudicated \
  temporal-kg-false-split-superseded \
  temporal-kg-runtime-unavailable \
  temporal-kg-provisional-identity \
  temporal-kg-projection-as-evidence \
  temporal-kg-missing-canonical-source \
  temporal-kg-missing-bitemporal-refs \
  temporal-kg-false-merge-without-adjudication \
  temporal-kg-false-split-without-supersession \
  temporal-kg-missing-replay
do
  uv run --python python3.12 --extra dev veracrawl-temporal-kg run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_temporal_kg_contracts.py \
  tests/contract/test_temporal_kg_contract_registry.py \
  tests/contract/test_temporal_kg_import_boundaries.py \
  tests/unit/test_temporal_kg_gate.py \
  tests/integration/test_temporal_kg_fixtures.py
```

Run registry and quality gates:

```bash
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration
```
