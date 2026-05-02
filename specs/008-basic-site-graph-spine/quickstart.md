# Quickstart: VeraCrawl Basic Site Graph Spine

This quickstart validates deterministic basic site graph contracts. It does not
claim advanced graph intelligence, memory intelligence, export delivery,
distributed persistence, production browser rendering, or production scale
readiness.

Run all graph fixtures:

```sh
for fixture in \
  graph-url-hyperlink \
  graph-canonical-redirect \
  graph-page-structure \
  graph-missing-input \
  graph-rebuild-mismatch \
  graph-as-evidence
do
  uv run --python python3.12 --extra dev veracrawl-graph run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Run the focused test gate:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_graph_contract_registry.py \
  tests/contract/test_graph_contracts.py \
  tests/contract/test_graph_import_boundaries.py \
  tests/unit/test_graph_build.py \
  tests/unit/test_graph_replay.py \
  tests/unit/test_graph_evidence_boundary.py \
  tests/integration/test_graph_fixtures.py
```
