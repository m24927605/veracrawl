# Tasks: Delivery ETA Offer Sorting Projection

## Implementation

- [x] T001 Add delivery ETA and shipping fee fields to product availability
  contracts.
- [x] T002 Add sortable offer projection contracts.
- [x] T003 Register offer projection contracts, commands, events, and target
  area coverage.
- [x] T004 Implement general source-backed ETA and shipping fee extraction.
- [x] T005 Implement offer sorting runtime for price, total price, delivery ETA,
  and availability.
- [x] T006 Extend product availability CLI JSON artifacts and summary.
- [x] T007 Add contract and focused runtime tests.
- [x] T008 Run registry validation.
- [x] T009 Run full ruff, mypy, pytest, and Docker-backed pytest if available.

## Validation Results

- Focused ruff passed:
  `uv run --python python3.12 --extra dev ruff check src/veracrawl/benchmarks/product_availability.py src/veracrawl/benchmarks/offer_projection.py src/veracrawl/cli/product_availability_benchmark.py src/veracrawl/contracts/product_availability.py src/veracrawl/contracts/offer_projection.py src/veracrawl/contracts/registry.py tests/unit/test_product_availability_runtime.py tests/unit/test_offer_projection_runtime.py tests/contract/test_offer_projection_contracts.py tests/contract/test_product_availability_contracts.py tests/contract/test_product_availability_contract_registry.py`.
- First focused pytest failed honestly because the new offer sorting test
  expected input-order tie behavior for equal availability rank. The runtime
  intentionally uses deterministic site-name tie-breaks; the test was corrected.
- Focused pytest passed:
  `uv run --python python3.12 --extra dev pytest tests/unit/test_offer_projection_runtime.py tests/unit/test_product_availability_runtime.py tests/contract/test_offer_projection_contracts.py tests/contract/test_product_availability_contracts.py tests/contract/test_product_availability_contract_registry.py -q`
  returned 26 passing tests.
- Focused mypy passed:
  `uv run --python python3.12 --extra dev mypy src/veracrawl/benchmarks/offer_projection.py src/veracrawl/benchmarks/product_availability.py src/veracrawl/cli/product_availability_benchmark.py src/veracrawl/contracts/offer_projection.py src/veracrawl/contracts/product_availability.py tests/unit/test_offer_projection_runtime.py tests/unit/test_product_availability_runtime.py tests/contract/test_offer_projection_contracts.py`
  returned no issues after fixing a nullable availability rank type error.
- Registry validation passed:
  `uv run --python python3.12 --extra dev veracrawl-contracts validate`
  returned `ok=true`, no errors, no warnings.
- Product availability fixture/import-boundary focused integration passed:
  `uv run --python python3.12 --extra dev pytest tests/integration/test_product_availability_fixtures.py tests/contract/test_contract_registry.py tests/contract/test_product_availability_import_boundaries.py -q`
  returned 14 passing tests.
- Full ruff passed:
  `uv run --python python3.12 --extra dev ruff check .`.
- Full mypy passed:
  `uv run --python python3.12 --extra dev mypy src tests` returned
  `Success: no issues found in 709 source files`.
- Full pytest passed:
  `uv run --python python3.12 --extra dev pytest -q` exited 0 after running the
  full test suite.
- Docker-backed pytest first skipped honestly without the required opt-in env:
  `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/integration/test_operational_infrastructure_live.py -q -rs`
  skipped with `set VERACRAWL_* live vars or VERACRAWL_INFRASTRUCTURE_DOCKER=1`.
- Docker-backed pytest passed after explicit opt-in:
  `VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/integration/test_operational_infrastructure_live.py -q -rs`
  returned 1 passing test.

## Live Ecommerce Offer Projection Results

- First Taiwan live run exposed a real extraction bug: momo `運費$75` was
  parsed as USD because the generic money parser treated bare `$` as USD. This
  was fixed so shipping fee extraction uses the product price currency when a
  shipping fee has a bare currency symbol and no explicit currency code.
- Post-fix Taiwan live run:
  `uv run --python python3.12 --extra dev veracrawl-product-availability-benchmark run tests/fixtures/taiwan-top-ecommerce-product-availability --profile target --out .veracrawl-real-runs/078-taiwan-offer-projection-http-fixed`
  returned `needs_review`, 2 sortable offers, 1 blocked offer. momo produced
  price `1879 TWD`, availability `out_of_stock`, ETA `1-1 days`, shipping fee
  `75 TWD`, total price `1954 TWD`. PChome produced price `1999 TWD`,
  availability `in_stock`, ETA `1-1 days`, free shipping, total price
  `1999 TWD`. Shopee remained blocked with JavaScript shell/source limitation.
- Post-fix US live run:
  `uv run --python python3.12 --extra dev veracrawl-product-availability-benchmark run tests/fixtures/us-top-ecommerce-product-availability --profile target --out .veracrawl-real-runs/078-us-offer-projection-http-fixed`
  returned `needs_review`, 2 sortable offers, 1 blocked offer. Walmart produced
  source-backed price/availability and ETA `2-2 days`; Amazon produced
  source-backed price/availability and free-shipping evidence but no
  source-backed delivery ETA. eBay remained blocked with missing network
  artifact/source limitation.
