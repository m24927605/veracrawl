# Quickstart: Delivery ETA Offer Sorting Projection

Run focused validation:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/unit/test_offer_projection_runtime.py \
  tests/unit/test_product_availability_runtime.py \
  tests/contract/test_offer_projection_contracts.py \
  tests/contract/test_product_availability_contracts.py \
  tests/contract/test_product_availability_contract_registry.py
```

Run the product availability CLI fixture and inspect sortable artifacts:

```bash
uv run --python python3.12 --extra dev pytest \
  tests/integration/test_product_availability_fixtures.py
```

Expected output files include:

- `run_report.json`
- `site_results.json`
- `field_evidence.json`
- `offer_records.json`
- `offer_projection_report.json`
- `summary.json`
