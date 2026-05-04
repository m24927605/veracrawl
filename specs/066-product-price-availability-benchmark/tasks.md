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

## Phase 6: Amazon Browser DOM Evidence Follow-Up

- [x] T024 Add product availability browser fallback and browser-source-required
  runtime mode without importing concrete browser engines into core.
- [x] T025 Add generic TWD text price and limited-stock availability extraction
  patterns for source-backed product pages.
- [x] T026 Add focused runtime tests for HTTP-missing browser recovery and forced
  browser DOM field evidence.
- [x] T027 Add CLI flags `--browser-fallback` and `--browser-source-required`.
- [x] T028 Run hosted OpenAI live benchmark with browser fallback.
- [x] T029 Run hosted OpenAI live benchmark with browser DOM source required and
  inspect Amazon field evidence.
- [x] T030 Record failed live attempt, fix, rerun result, and validations.

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
- Amazon browser follow-up focused tests:
  `uv run --python python3.12 --extra dev pytest tests/unit/test_product_availability_runtime.py -q`
  reported `8 passed`.
- Amazon browser follow-up ruff:
  `uv run --python python3.12 --extra dev ruff check src/veracrawl/benchmarks/product_availability.py src/veracrawl/cli/product_availability_benchmark.py tests/unit/test_product_availability_runtime.py`
  passed.
- Amazon browser follow-up mypy:
  `uv run --python python3.12 --extra dev mypy src/veracrawl/benchmarks/product_availability.py src/veracrawl/cli/product_availability_benchmark.py tests/unit/test_product_availability_runtime.py`
  passed with no issues.
- Hosted OpenAI live browser fallback run:
  `uv run --python python3.12 --extra dev --extra browser-playwright veracrawl-product-availability-benchmark run tests/fixtures/us-top-ecommerce-product-availability --profile target --model-provider openai --openai-model gpt-5.4-mini --browser-fallback --out .veracrawl-real-runs/us-top-ecommerce-product-availability-openai-browser-fallback`
  reported `completion_result=needs_review`,
  `operator_status=product_availability_partial_sources_blocked`,
  `site_count=3`, `passing_site_count=2`, `blocked_site_count=1`,
  `field_evidence_count=6`, `price_evidence_count=2`,
  `availability_evidence_count=2`, and 8 model/agent/tool/context traces.
  Amazon passed from source-backed HTTP HTML after the generic limited-stock
  extractor matched `Only 9 left in stock - order soon.`; this showed the
  earlier Amazon availability problem was also an extractor-pattern gap, not
  only a browser-rendering gap.
- First hosted OpenAI live browser-source-required run failed before producing a
  benchmark report:
  `uv run --python python3.12 --extra dev --extra browser-playwright veracrawl-product-availability-benchmark run tests/fixtures/us-top-ecommerce-product-availability --profile target --model-provider openai --openai-model gpt-5.4-mini --browser-source-required --out .veracrawl-real-runs/us-top-ecommerce-product-availability-openai-browser-source-required`
  raised Playwright `Page.wait_for_function: Timeout 30000ms exceeded` while
  waiting for a required identity fragment. Fixed by making product availability
  browser observation not depend on a forced fragment wait and by mapping browser
  adapter exceptions to typed source-limited outcomes instead of crashing.
- Hosted OpenAI live browser-source-required rerun:
  `uv run --python python3.12 --extra dev --extra browser-playwright veracrawl-product-availability-benchmark run tests/fixtures/us-top-ecommerce-product-availability --profile target --model-provider openai --openai-model gpt-5.4-mini --browser-source-required --out .veracrawl-real-runs/us-top-ecommerce-product-availability-openai-browser-source-required`
  reported `completion_result=needs_review`,
  `operator_status=product_availability_partial_sources_blocked`,
  `site_count=3`, `passing_site_count=1`, `blocked_site_count=2`,
  `field_evidence_count=3`, `price_evidence_count=1`,
  `availability_evidence_count=1`, and 4 OpenAI model/agent/tool/context traces.
  Amazon passed with browser DOM field artifact
  `artifact:us-top-ecommerce-product-availability:us-amazon-sandisk-256gb-extreme:browser-render:dom:71df7966373c`,
  browser DOM content hash
  `71df7966373c5ebe11788c884b7f1393079739f0e3d6e38f4154050dfc79a030`,
  price `TWD1,876.17`, amount `1876.17`, currency `TWD`, and availability
  `limited` from raw text `Only 9 left in stock - order soon.`. The accepted
  Amazon fields also carried OpenAI `gpt-5.4-mini` model call traces, native
  agent action traces, tool call traces, context bundle traces, source anchors,
  verification decisions, command/event/outbox refs, and replay refs. Walmart
  browser-source-required failed product identity match in this run, and eBay
  remained source-access denied; neither was fabricated as successful.
- Post-follow-up focused 066 suite:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_product_availability_contracts.py tests/contract/test_product_availability_contract_registry.py tests/contract/test_product_availability_import_boundaries.py tests/unit/test_product_availability_runtime.py tests/unit/test_product_availability_replay.py tests/integration/test_product_availability_fixtures.py -q`
  reported `27 passed`.
- Post-follow-up registry validation:
  `uv run --python python3.12 --extra dev veracrawl-contracts validate`
  reported `ok=true` with no registry errors.
- Post-follow-up full ruff:
  `uv run --python python3.12 --extra dev ruff check .` passed.
- Post-follow-up full mypy:
  `uv run --python python3.12 --extra dev mypy src tests` passed with no issues
  across 694 source files.
- Post-follow-up full pytest:
  `uv run --python python3.12 --extra dev pytest -q` exited with code 0 and
  reached `[100%]` with no failures in the emitted output.
- Post-follow-up Docker-backed operational focused pytest:
  `VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/integration/test_operational_infrastructure_live.py -q`
  reported `1 passed`.
- Post-follow-up `git diff --check` first failed on trailing whitespace in
  `specs/066-product-price-availability-benchmark/plan.md`; the whitespace was
  fixed and the rerun passed with no output.
- After the final diagnostic wording cleanup, `uv run --python python3.12 --extra dev pytest tests/unit/test_product_availability_runtime.py -q`
  reported `8 passed`, `uv run --python python3.12 --extra dev ruff check src/veracrawl/benchmarks/product_availability.py`
  passed, and `uv run --python python3.12 --extra dev mypy src/veracrawl/benchmarks/product_availability.py`
  passed with no issues.
- Walmart browser source classification follow-up:
  a manual Playwright probe of `https://www.walmart.com/ip/264401664` rendered
  `Robot or human? Activate and hold the button to confirm that you're human.`
  with no product identity, price, or availability terms. The runtime now
  classifies browser-rendered human-check/access-control pages as
  `product_availability_source_access_denied` instead of
  `product_availability_identity_mismatch`.
- Walmart classification focused tests:
  `uv run --python python3.12 --extra dev pytest tests/unit/test_product_availability_runtime.py -q`
  reported `9 passed`, `uv run --python python3.12 --extra dev ruff check src/veracrawl/benchmarks/product_availability.py tests/unit/test_product_availability_runtime.py`
  passed, and `uv run --python python3.12 --extra dev mypy src/veracrawl/benchmarks/product_availability.py tests/unit/test_product_availability_runtime.py`
  passed with no issues.
- Hosted OpenAI live browser-source-required Walmart rerun:
  `uv run --python python3.12 --extra dev --extra browser-playwright veracrawl-product-availability-benchmark run tests/fixtures/us-top-ecommerce-product-availability --profile target --model-provider openai --openai-model gpt-5.4-mini --browser-source-required --out .veracrawl-real-runs/us-top-ecommerce-product-availability-openai-browser-source-required-walmart-classified`
  reported `completion_result=needs_review`,
  `operator_status=product_availability_partial_sources_blocked`,
  `site_count=3`, `passing_site_count=1`, `blocked_site_count=2`,
  `field_evidence_count=3`, `price_evidence_count=1`,
  `availability_evidence_count=1`, and 4 OpenAI model/agent/tool/context traces.
  Amazon remained passing with browser DOM evidence for price `TWD1,876.17` and
  availability `limited`; Walmart was correctly recorded as
  `product_availability_source_access_denied` with missing field
  `browser_dom_source`; eBay remained source-access denied.
