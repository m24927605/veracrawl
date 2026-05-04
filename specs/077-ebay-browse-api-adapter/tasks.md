# Tasks: eBay Browse API Adapter

## Implementation

- [x] T001 Reuse shared official ecommerce API contracts.
- [x] T002 Implement `EbayBrowseApiAdapter`.
- [x] T003 Support `EBAY_ACCESS_TOKEN` and OAuth client-credentials flow.
- [x] T004 Add eBay target to shared US official API fixture.
- [x] T005 Add unit and integration tests.
- [x] T006 Record validation results.

## Validation Results

- Focused pytest passed:
  `uv run --python python3.12 --extra dev pytest tests/unit/test_ecommerce_official_api_runtime.py tests/unit/test_ecommerce_official_api_adapters.py tests/integration/test_ecommerce_official_api_cli.py tests/contract/test_contract_registry.py`
  returned 12 passing tests.
- Focused ruff passed:
  `uv run --python python3.12 --extra dev ruff check src/veracrawl/contracts/ecommerce_official_api.py src/veracrawl/ports/ecommerce_official_api.py src/veracrawl/benchmarks/ecommerce_official_api.py src/veracrawl/adapters/official_apis src/veracrawl/cli/ecommerce_official_api.py tests/unit/test_ecommerce_official_api_runtime.py tests/unit/test_ecommerce_official_api_adapters.py tests/integration/test_ecommerce_official_api_cli.py`.
- Focused mypy passed:
  `uv run --python python3.12 --extra dev mypy src/veracrawl/contracts/registry.py src/veracrawl/contracts/ecommerce_official_api.py src/veracrawl/ports/ecommerce_official_api.py src/veracrawl/benchmarks/ecommerce_official_api.py src/veracrawl/adapters/official_apis src/veracrawl/cli/ecommerce_official_api.py tests/unit/test_ecommerce_official_api_runtime.py tests/unit/test_ecommerce_official_api_adapters.py tests/integration/test_ecommerce_official_api_cli.py tests/contract/test_contract_registry.py`.
- Registry validation passed:
  `uv run --python python3.12 --extra dev veracrawl-contracts validate`
  returned `ok=True`, no errors, no warnings.
- Live no-credential CLI run passed honestly:
  `uv run --python python3.12 --extra dev veracrawl-ecommerce-official-api run-live tests/fixtures/us-ecommerce-official-api-product-availability --profile target --out .veracrawl-test-runs/us-ecommerce-official-api-product-availability`
  returned `completion_result=needs_review`,
  `operator_status=ecommerce_official_api_credentials_required`, `0/2` passing
  sites, and `2` blocked sites.
- First full pytest run failed honestly because
  `src/veracrawl/cli/ecommerce_official_api.py` statically imported concrete
  Amazon/eBay adapters and violated import-boundary tests. The CLI was fixed to
  lazy-load concrete adapters via `importlib`.
- Full ruff passed:
  `uv run --python python3.12 --extra dev ruff check .`.
- Full mypy passed:
  `uv run --python python3.12 --extra dev mypy src tests` returned
  `Success: no issues found in 705 source files`.
- Full pytest rerun passed:
  `uv run --python python3.12 --extra dev pytest -q`.
- Final registry validation passed:
  `uv run --python python3.12 --extra dev veracrawl-contracts validate`
  returned `ok=True`, no errors, no warnings.
- Final live no-credential CLI run passed honestly at
  `.veracrawl-test-runs/us-ecommerce-official-api-product-availability-final`
  with `completion_result=needs_review`,
  `operator_status=ecommerce_official_api_credentials_required`, `0/2` passing
  sites, and `2` blocked sites.
- eBay credentialed live pass was NOT claimed because no eBay client
  credentials or access token were provided.
