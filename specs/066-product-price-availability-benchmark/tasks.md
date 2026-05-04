# Tasks: US Top Ecommerce Product Price Availability Benchmark

## Phase 1: Spec Kit Setup

- [x] T001 Create `066-product-price-availability-benchmark` branch and activate
  feature context.
- [x] T002 Add spec, research, data model, contract, quickstart, plan, and tasks.
- [x] T003 Update `AGENTS.md`, `README.md`, `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`, and
  `docs/11-target-testing-and-acceptance.md`.

## Phase 2: Contracts And Runtime

- [x] T004 Add product availability enums and contracts.
- [x] T005 Export contracts and register registry commands/events/fixture/area.
- [x] T006 Implement product availability runtime and replay helpers.
- [x] T007 Add CLI entry point.

## Phase 3: Fixtures And Tests

- [x] T008 Add positive live fixture for US top ecommerce product pages.
- [x] T009 Add negative fixtures for wrong identity, missing price, missing
  availability, LLM-as-evidence, and missing replay.
- [x] T010 Add contract, registry, import-boundary, unit, replay, and integration
  tests.

## Phase 4: Live Experiments

- [x] T011 Run deterministic/local benchmark.
- [x] T012 Run hosted OpenAI benchmark.
- [x] T013 Inspect extracted prices, availability statuses, trace counts, and
  blocked source outcomes.

## Phase 5: Validation

- [x] T014 Run Spec Kit prerequisite check.
- [x] T015 Run ruff.
- [x] T016 Run mypy.
- [x] T017 Run registry validation.
- [x] T018 Run focused 066 tests.
- [x] T019 Run full pytest.
- [x] T020 Run Docker-backed pytest.
- [x] T021 Run `git diff --check`.
- [x] T022 Record validation outputs in this file.
- [x] T023 Commit and fast-forward merge 066.

## Validation Results

- Initial live probe on 2026-05-04:
  Amazon SanDisk 256GB Extreme microSDXC UHS-I Memory Card with Adapter product page returned HTTP 200 with product
  identity terms and observed localized price marker `TWD1,866.69`; Walmart
  SanDisk 256GB Extreme microSDXC UHS-I Memory Card with Adapter product page returned HTTP 200 with product identity
  terms, `price=82.68`, and `https://schema.org/OutOfStock`; eBay item page probes
  returned HTTP 403 Access Denied to the benchmark HTTP adapter. This will be
  treated as a typed blocked-source outcome, not a fabricated extraction.
- Focused 066 tests after implementation:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_product_availability_contracts.py tests/contract/test_product_availability_contract_registry.py tests/contract/test_product_availability_import_boundaries.py tests/unit/test_product_availability_runtime.py tests/unit/test_product_availability_replay.py tests/integration/test_product_availability_fixtures.py`
  reported `21 passed in 0.84s`.
- Deterministic/local live product benchmark:
  `uv run --python python3.12 --extra dev veracrawl-product-availability-benchmark run tests/fixtures/us-top-ecommerce-product-availability --profile target --out .veracrawl-real-runs/us-top-ecommerce-product-availability`
  reported `completion_result=needs_review`,
  `operator_status=product_availability_partial_sources_blocked`,
  `site_count=3`, `passing_site_count=2`, `blocked_site_count=1`,
  `field_evidence_count=6`, `price_evidence_count=2`,
  `availability_evidence_count=2`, and 8 model/agent/tool/context traces.
- Local live extracted fields:
  Amazon passed with price `TWD1,867.00`, amount `1867.0`, currency `TWD`, and
  availability `in_stock`; Walmart passed with price `$75.00`, currency `USD`,
  and availability `in_stock`; eBay returned `needs_review` with no price or
  availability, failure type `product_availability_source_access_denied`, and
  diagnostics `missing_network_artifact`.
- Hosted OpenAI live product benchmark:
  `uv run --python python3.12 --extra dev veracrawl-product-availability-benchmark run tests/fixtures/us-top-ecommerce-product-availability --profile target --model-provider openai --openai-model gpt-5.4-mini --out .veracrawl-real-runs/us-top-ecommerce-product-availability-openai`
  reported `completion_result=needs_review`,
  `operator_status=product_availability_partial_sources_blocked`,
  `site_count=3`, `passing_site_count=2`, `blocked_site_count=1`,
  `field_evidence_count=6`, `price_evidence_count=2`,
  `availability_evidence_count=2`, and 8 model/agent/tool/context traces.
- Hosted OpenAI trace inspection passed:
  `model_call_traces=8`, `agent_action_traces=8`, `tool_call_traces=8`,
  `context_bundle_traces=8`, and `field_evidence=6`. First
  `ModelCallTrace` recorded provider `OpenAI Responses API`, model
  `gpt-5.4-mini`, token usage `input_tokens=240`, `output_tokens=74`,
  `total_tokens=314`, `raw_prompt_persisted=false`, and
  `raw_response_persisted=false`.
- Hosted OpenAI extracted fields:
  Amazon passed with price `TWD1,867.00`, amount `1867.0`, currency `TWD`, and
  availability `in_stock`; Walmart passed with price `USD 82.68`, amount
  `82.68`, currency `USD`, and availability `out_of_stock`; eBay returned
  `needs_review` with no price or availability, failure type
  `product_availability_source_access_denied`, and diagnostics
  `missing_network_artifact`.
- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  completed successfully for `066-product-price-availability-benchmark`.
- `uv run --python python3.12 --extra dev ruff check .` passed after fixing line
  length and unused import issues.
- `uv run --python python3.12 --extra dev mypy src tests` passed with no issues
  across 680 source files.
- Registry validation passed:
  `uv run --python python3.12 --extra dev python -c 'from veracrawl.contracts.registry import validate_registry; print(validate_registry().model_dump_json(indent=2))'`
  reported `ok=true`, no errors, and no warnings.
- Focused 066 tests passed:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_product_availability_contracts.py tests/contract/test_product_availability_contract_registry.py tests/contract/test_product_availability_import_boundaries.py tests/unit/test_product_availability_runtime.py tests/unit/test_product_availability_replay.py tests/integration/test_product_availability_fixtures.py`
  reported `21 passed in 0.86s`.
- First full pytest run:
  `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  failed in `tests/contract/test_contract_registry.py::test_target_contract_area_coverage_is_explicit`
  because `product_availability_benchmark_gate` was not included in the
  explicit target-area coverage assertion. Fixed by updating
  `tests/contract/test_contract_registry.py`.
- Full pytest rerun passed:
  `uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  reported `1277 passed, 5 skipped in 239.71s`.
- Docker-backed pytest passed:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  reported `1282 passed in 269.33s`.
- `git diff --check` passed with no whitespace errors.
