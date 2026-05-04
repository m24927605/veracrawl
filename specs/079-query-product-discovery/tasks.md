# Tasks: Query Product Discovery And Offer Ranking

## Phase 1: Spec Kit Setup

- [x] T001 Create `079-query-product-discovery` branch and feature directory.
- [x] T002 Add spec, research, data model, contract notes, quickstart, plan, and
  tasks.
- [x] T003 Update `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`,
  `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`,
  `README.md`, and `AGENTS.md`.

## Phase 2: Contracts And Runtime

- [x] T004 Add product discovery contracts.
- [x] T005 Register product discovery contracts, commands, events, fixture
  oracles, and target-area coverage.
- [x] T006 Implement query discovery runtime with source-backed candidate URL
  extraction and framework-neutral AI traces.
- [x] T007 Compose discovered candidates into product availability and offer
  projection runtime.
- [x] T008 Improve product identity matching so rejected variant terms are
  evaluated against product identity text where available.
- [x] T009 Add CLI entry point and JSON artifacts.

## Phase 3: Fixtures And Tests

- [x] T010 Add positive query discovery fixture with only search/listing URLs.
- [x] T011 Add negative no-candidates fixture.
- [x] T012 Add contract, registry, import-boundary, unit, replay, and integration
  tests.

## Phase 4: Live Experiment

- [x] T013 Add Taiwan iPhone 17 256G query fixture using public ecommerce search
  entry pages only.
- [x] T014 Run live local query discovery.
- [x] T015 Run hosted OpenAI query discovery.
- [x] T016 Inspect discovered candidates, excluded candidates, ranked offers, and
  source-limited outcomes.

## Phase 5: Validation

- [x] T017 Run Spec Kit prerequisite check.
- [x] T018 Run ruff.
- [x] T019 Run mypy.
- [x] T020 Run registry validation.
- [x] T021 Run focused 079 tests.
- [x] T022 Run full pytest.
- [x] T023 Run Docker-backed pytest if available.
- [x] T024 Run `git diff --check`.
- [x] T025 Record validation outputs in this file.
- [x] T026 Commit and fast-forward merge 079.

## Validation Results

- Spec Kit prerequisite check:
  `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  returned feature dir `specs/079-query-product-discovery` with `research.md`,
  `data-model.md`, `contracts/`, `quickstart.md`, and `tasks.md`.
- Live local query discovery:
  `uv run --python python3.12 --extra dev veracrawl-product-discovery run tests/fixtures/taiwan-iphone17-query-product-discovery --profile target --out .veracrawl-real-runs/taiwan-iphone17-query-product-discovery`
  returned `ok: true`, `completion_result: needs_review`,
  `operator_status: product_discovery_partial_sources_blocked`, 20 discovered
  source-backed candidates, 20 accepted candidates, 10 ranked offers, 42 model
  call traces, 42 agent action traces, 42 tool call traces, 42 context bundle
  traces, 10 passing PChome product pages, and 10 Yahoo product pages blocked by
  source access denial. The fixture input contains search/listing URLs only; no
  manually supplied product target URLs.
- Hosted OpenAI query discovery:
  `set -a; source ~/.env; set +a; uv run --python python3.12 --extra dev veracrawl-product-discovery run tests/fixtures/taiwan-iphone17-query-product-discovery --profile target --model-provider openai --openai-model gpt-5.4-mini --out .veracrawl-real-runs/taiwan-iphone17-query-product-discovery-openai`
  returned `ok: true`, `completion_result: needs_review`,
  `operator_status: product_discovery_partial_sources_blocked`, 20 accepted
  candidates, 10 ranked offers, 42 model call traces, 42 agent action traces, 42
  tool call traces, 42 context bundle traces, and OpenAI response refs. Model
  response statuses were 40 `completed` and 2 `incomplete`; this is recorded as
  a real hosted LLM run, not as an all-completed publication pass.
- `uv run --python python3.12 --extra dev ruff check .`: passed.
- `uv run --python python3.12 --extra dev mypy src tests`: passed with no issues
  in 717 source files.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate`: passed
  with `ok: true` and no registry warnings.
- `uv run --python python3.12 --extra dev pytest tests/contract/test_product_discovery_contracts.py tests/contract/test_product_discovery_contract_registry.py tests/contract/test_product_discovery_import_boundaries.py tests/unit/test_product_discovery_runtime.py tests/integration/test_product_discovery_fixtures.py tests/unit/test_product_availability_runtime.py tests/contract/test_contract_registry.py tests/contract/test_product_availability_contract_registry.py -q`:
  passed.
- `uv run --python python3.12 --extra dev pytest -q`: passed.
- `VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/integration/test_operational_infrastructure_live.py -q -rs`:
  passed (`1 passed`).
- `git diff --check`: passed with no whitespace errors.
