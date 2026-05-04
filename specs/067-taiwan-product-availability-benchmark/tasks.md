# Tasks: Taiwan Top Ecommerce Product Price Availability Benchmark

## Phase 1: Spec Kit Setup

- [x] T001 Create `067-taiwan-product-availability-benchmark` branch and activate
  feature context.
- [x] T002 Add spec, research, data model, contract, quickstart, plan, and tasks.
- [x] T003 Amend `docs/08-build-roadmap.md`, `docs/07-data-contracts.md`,
  `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`,
  `README.md`, and `AGENTS.md`.

## Phase 2: Runtime And Fixture

- [x] T004 Add generic Taiwan/meta price extraction support.
- [x] T005 Add generic product meta and Chinese availability extraction support.
- [x] T006 Add Taiwan top ecommerce product availability fixture and oracles.
- [x] T007 Register the Taiwan fixture in the contract registry.

## Phase 3: Tests

- [x] T008 Add unit tests for product meta price/availability extraction.
- [x] T009 Add Taiwan fixture to focused integration coverage.
- [x] T010 Run focused product availability tests.

## Phase 4: Live Experiments

- [x] T011 Run deterministic/local Taiwan benchmark.
- [x] T012 Run hosted OpenAI Taiwan benchmark.
- [x] T013 Inspect extracted prices, availability statuses, trace counts, and
  Shopee source-limited outcome.

## Phase 5: Validation

- [x] T014 Run Spec Kit prerequisite check.
- [x] T015 Run ruff.
- [x] T016 Run mypy.
- [x] T017 Run registry validation.
- [x] T018 Run focused 067 tests.
- [x] T019 Run full pytest.
- [x] T020 Run `git diff --check`.
- [x] T021 Record validation outputs in this file.
- [x] T022 Commit and fast-forward merge 067.

## Validation Results

- Initial live probe on 2026-05-04:
  Shopee Taiwan product page returned HTTP 200 but only a JavaScript application
  shell and direct product API probes returned HTTP 403. momo product page
  returned public product meta tags with `product:price:amount=1,879`,
  `product:price:currency=TWD`, and `product:availability=in stock`. PChome 24h
  product page returned JSON-LD Product/Offer with `price=1999`,
  `priceCurrency=TWD`, and `availability=http://schema.org/InStock`.
- Spec Kit prerequisite check passed:
  `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  returned the 067 feature directory with `research.md`, `data-model.md`,
  `contracts/`, `quickstart.md`, and `tasks.md`.
- Focused runtime/fixture/registry tests passed:
  `uv run --python python3.12 --extra dev pytest tests/unit/test_product_availability_runtime.py tests/integration/test_product_availability_fixtures.py tests/contract/test_product_availability_contract_registry.py`
  returned `16 passed`.
- Focused product availability contract/import/replay/integration suite passed:
  `uv run --python python3.12 --extra dev pytest tests/contract/test_product_availability_contracts.py tests/contract/test_product_availability_contract_registry.py tests/contract/test_product_availability_import_boundaries.py tests/unit/test_product_availability_runtime.py tests/unit/test_product_availability_replay.py tests/integration/test_product_availability_fixtures.py`
  returned `25 passed`.
- Deterministic/local live Taiwan benchmark passed with honest needs-review:
  `uv run --python python3.12 --extra dev veracrawl-product-availability-benchmark run tests/fixtures/taiwan-top-ecommerce-product-availability --profile target --out .veracrawl-real-runs/taiwan-top-ecommerce-product-availability`
  returned `ok=true`, `completion_result=needs_review`, `passing_site_count=2`,
  `blocked_site_count=1`, `model_call_trace_count=8`,
  `agent_action_trace_count=8`, `tool_call_trace_count=8`,
  `context_bundle_trace_count=8`, `field_evidence_count=6`,
  `price_evidence_count=2`, and `availability_evidence_count=2`.
- Local benchmark site outputs:
  Shopee Taiwan returned `needs_review` with
  `product_availability_source_access_denied` because live HTML was a JavaScript
  application shell without source-backed product identity. momo returned
  `pass`, price `TWD 1879`, availability `in_stock`. PChome 24h returned
  `pass`, price `TWD 1999`, availability `in_stock`.
- Hosted OpenAI live Taiwan benchmark passed:
  `set -a; source ~/.env; set +a; uv run --python python3.12 --extra dev veracrawl-product-availability-benchmark run tests/fixtures/taiwan-top-ecommerce-product-availability --profile target --model-provider openai --openai-model gpt-5.4-mini --out .veracrawl-real-runs/taiwan-top-ecommerce-product-availability-openai`
  returned `ok=true`, `completion_result=needs_review`, `passing_site_count=2`,
  `blocked_site_count=1`, and eight `OpenAI Responses API` model call traces
  using `gpt-5.4-mini`.
- Hosted OpenAI evidence inspection confirmed six field evidence rows. momo and
  PChome 24h price/availability evidence each carry source anchors, artifact
  refs, content hashes, model call trace refs, agent action/tool/context refs,
  policy refs, command/event/outbox refs, and replay refs. Shopee Taiwan has no
  fabricated price, availability, or field evidence.
- Ruff passed:
  `uv run --python python3.12 --extra dev ruff check .`
  returned `All checks passed!`.
- Mypy passed:
  `uv run --python python3.12 --extra dev mypy src tests`
  returned `Success: no issues found in 680 source files`.
- Registry validation passed:
  `uv run --python python3.12 --extra dev python -c 'from veracrawl.contracts.registry import validate_registry; print(validate_registry().model_dump_json(indent=2))'`
  returned `ok=true` with no errors or warnings.
- Full pytest passed:
  `uv run --python python3.12 --extra dev pytest`
  returned `1281 passed, 5 skipped`.
- Docker-backed full pytest passed:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1 VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 VERACRAWL_DR_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest`
  returned `1286 passed`.
- Whitespace diff validation passed:
  `git diff --check` returned no output.
