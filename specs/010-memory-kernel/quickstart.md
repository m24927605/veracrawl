# Quickstart: VeraCrawl Memory Kernel

Run focused tests:

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_memory_contract_registry.py \
  tests/contract/test_memory_contracts.py \
  tests/contract/test_memory_import_boundaries.py \
  tests/unit/test_memory_kernel.py \
  tests/unit/test_memory_retrieval.py \
  tests/unit/test_memory_replay.py \
  tests/unit/test_memory_evidence_boundary.py \
  tests/unit/test_cross_scope_memory_policy.py \
  tests/integration/test_memory_fixtures.py
```

Run memory fixtures:

```sh
for fixture in \
  memory-write-retrieve-success \
  memory-invalidation-exclusion \
  cross-scope-sanitized-memory \
  poisoned-memory-blocked \
  unauthorized-cross-scope-memory \
  memory-as-evidence
do
  uv run --python python3.12 --extra dev veracrawl-memory run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```
