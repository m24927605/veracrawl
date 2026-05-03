# Quickstart: Product Acceptance Gate

Run focused tests:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_product_acceptance_contracts.py \
  tests/contract/test_product_acceptance_contract_registry.py \
  tests/contract/test_product_acceptance_import_boundaries.py \
  tests/unit/test_product_acceptance_gate.py \
  tests/integration/test_product_acceptance_fixtures.py
```

Run the success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-product-acceptance run \
  tests/fixtures/product-acceptance-success \
  --profile target \
  --out .veracrawl-test-runs/product-acceptance-success
```

Run all product acceptance fixtures:

```bash
for fixture in \
  product-acceptance-success \
  product-acceptance-runtime-unavailable \
  product-acceptance-missing-workflow \
  product-acceptance-missing-minimum-gate \
  product-acceptance-missing-evidence \
  product-acceptance-missing-replay \
  product-acceptance-missing-operator-visibility \
  product-acceptance-missing-policy \
  product-acceptance-missing-workflow-specific-refs \
  product-acceptance-scaffold-only \
  product-acceptance-contract-only \
  product-acceptance-false-complete-status \
  product-acceptance-degraded-operational \
  product-acceptance-missing-export-reconciliation
do
  uv run --python python3.12 --extra dev veracrawl-product-acceptance run \
    "tests/fixtures/${fixture}" \
    --profile target \
    --out ".veracrawl-test-runs/${fixture}"
done
```
