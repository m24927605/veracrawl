# Tasks: JavaScript Browser Crawl Quality Benchmark

**Input**: Design documents from `/specs/059-js-browser-crawl-quality-benchmark/`
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/

**Tests**: Contract, registry, import-boundary, unit, integration, replay,
negative fixture, focused, full, Docker-backed, and live browser CLI validation
are required before marking this spec complete.

## Phase 1: Setup

- [x] T001 Activate `059-js-browser-crawl-quality-benchmark` Spec Kit feature context.
- [x] T002 Add 059 plan, research, data model, contract, quickstart, and tasks artifacts.
- [x] T003 Update `AGENTS.md` active Spec Kit pointer to 059.
- [x] T004 Update `README.md`, `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md` for 059 boundaries and commands.

## Phase 2: Foundational Contracts

- [x] T005 Add browser quality failure enum in `src/veracrawl/contracts/enums.py`.
- [x] T006 Add browser quality contracts in `src/veracrawl/contracts/browser_quality.py`.
- [x] T007 Export browser quality contracts in `src/veracrawl/contracts/__init__.py`.
- [x] T008 Extend browser port result metadata in `src/veracrawl/ports/browser.py`.
- [x] T009 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`.
- [x] T010 Add contract tests in `tests/contract/test_browser_quality_contracts.py`.
- [x] T011 Add registry tests in `tests/contract/test_browser_quality_contract_registry.py`.
- [x] T012 Add import-boundary tests in `tests/contract/test_browser_quality_import_boundaries.py`.

## Phase 3: Runtime, Adapter, And Replay

- [x] T013 Implement browser quality runtime in `src/veracrawl/benchmarks/browser_quality.py`.
- [x] T014 Implement adapter-owned Playwright browser adapter in `src/veracrawl/adapters/browser/playwright.py`.
- [x] T015 Implement replay checks in `src/veracrawl/review_replay/browser_quality.py`.
- [x] T016 Add runtime tests in `tests/unit/test_browser_quality_runtime.py`.
- [x] T017 Add replay tests in `tests/unit/test_browser_quality_replay.py`.

## Phase 4: CLI And Fixtures

- [x] T018 Add `veracrawl-browser-quality-benchmark` CLI in `src/veracrawl/cli/browser_quality.py`.
- [x] T019 Register CLI entry point and optional Playwright extra in `pyproject.toml`.
- [x] T020 Add success fixture in `tests/fixtures/browser-quality-corpus`.
- [x] T021 Add negative fixture `tests/fixtures/browser-quality-unsafe-action`.
- [x] T022 Add negative fixture `tests/fixtures/browser-quality-prompt-taint`.
- [x] T023 Add negative fixture `tests/fixtures/browser-quality-missing-artifact`.
- [x] T024 Add negative fixture `tests/fixtures/browser-quality-budget-exceeded`.
- [x] T025 Add negative fixture `tests/fixtures/browser-quality-replay-mismatch`.
- [x] T026 Add integration fixture tests in `tests/integration/test_browser_quality_fixtures.py`.

## Phase 5: Validation

- [x] T027 Run Spec Kit prerequisite check for 059.
- [x] T028 Run `uv lock` after adding optional browser dependency.
- [x] T029 Run ruff.
- [x] T030 Run mypy.
- [x] T031 Run registry validation.
- [x] T032 Run focused 059 tests.
- [x] T033 Run deterministic browser quality CLI validation.
- [x] T034 Install Playwright Chromium for live validation.
- [x] T035 Run live public browser quality CLI validation with Playwright.
- [x] T036 Run full pytest.
- [x] T037 Run Docker-backed pytest.
- [x] T038 Run `git diff --check`.
- [x] T039 Record all validation outputs in this file.
- [x] T040 Verify no docs, code, CLI output, or tests claim deep crawl, credentialed browsing, CAPTCHA solving, stealth automation, field-level oracle, precision/recall, repair, or production-quality release completion.

## Validation Results

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  passed for `specs/059-js-browser-crawl-quality-benchmark` with
  `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and
  `tasks.md` available.
- `uv lock` resolved successfully after adding the optional
  `browser-playwright` extra.
- `uv run --python python3.12 --extra dev ruff check .`: all checks passed.
- `uv run --python python3.12 --extra dev mypy src tests`: success across 620
  source files.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate
  --format json`: registry validation returned `ok: true`, `errors: []`,
  `warnings: []`, and `target_area_count: 63`.
- Focused 059 pytest gate:
  `tests/contract/test_browser_quality_contracts.py`,
  `tests/contract/test_browser_quality_contract_registry.py`,
  `tests/contract/test_browser_quality_import_boundaries.py`,
  `tests/unit/test_browser_quality_runtime.py`,
  `tests/unit/test_browser_quality_replay.py`, and
  `tests/integration/test_browser_quality_fixtures.py` passed with
  `23 passed in 2.44s`.
- Deterministic browser quality CLI gate:
  `uv run --python python3.12 --extra dev veracrawl-browser-quality-benchmark
  run tests/fixtures/browser-quality-corpus --profile quality
  --browser-adapter deterministic --out .veracrawl-test-runs/browser-quality-corpus`
  returned `ok: true`, `completion_result: pass`, `operator_status:
  browser_quality_completed`, `target_count: 8`,
  `browser_required_pass_count: 8`, `recovered_fragment_count: 8`,
  `http_only_missing_count: 8`, `dom_artifact_count: 8`,
  `screenshot_artifact_count: 8`, and `replay_bundle_count: 8`.
- Playwright browser runtime install:
  `uv run --python python3.12 --extra browser-playwright python -m playwright
  install chromium` exited successfully. The first live CLI attempt exposed a
  real adapter bug: `Page.wait_for_function()` was called with the fragment as
  a positional argument. The adapter was corrected to use `arg=fragment` before
  marking the live gate complete.
- Live public browser quality CLI gate:
  `uv run --python python3.12 --extra dev --extra browser-playwright
  veracrawl-browser-quality-benchmark run tests/fixtures/browser-quality-corpus
  --profile quality --browser-adapter playwright --out
  .veracrawl-real-runs/browser-quality-corpus` returned `ok: true`,
  `completion_result: pass`, `operator_status: browser_quality_completed`,
  `target_count: 8`, `browser_required_pass_count: 8`,
  `recovered_fragment_count: 8`, `http_only_missing_count: 8`,
  `dom_artifact_count: 8`, `screenshot_artifact_count: 8`, and
  `replay_bundle_count: 8`; the report recorded no budget, unsafe-action,
  prompt-taint, artifact-missing, or replay-missing failures.
- Full non-Docker pytest gate:
  `uv run --python python3.12 --extra dev pytest` passed with `1103 passed,
  5 skipped in 186.54s`.
- Docker-backed pytest gate:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1
  VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python
  python3.12 --extra dev --extra postgres --extra queue-redis --extra
  object-s3 pytest` passed with `1108 passed in 200.68s`.
- `git diff --check`: passed.
- Boundary check: `rg` confirmed 059-facing docs describe bounded deep crawl,
  credentialed browsing, CAPTCHA solving, stealth automation, field-level
  oracle extraction, precision/recall, repair success, and final
  production-quality release readiness as out of scope for this spec or as
  later roadmap work rather than claimed complete by 059.
