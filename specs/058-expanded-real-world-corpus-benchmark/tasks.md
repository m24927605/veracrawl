# Tasks: Expanded Real-World Public Corpus Benchmark

**Input**: Design documents from `/specs/058-expanded-real-world-corpus-benchmark/`
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/

**Tests**: Contract, registry, import-boundary, unit, integration, replay,
negative fixture, focused, full, Docker-backed, and live CLI validation are
required before marking this spec complete.

## Phase 1: Setup

- [x] T001 Activate `058-expanded-real-world-corpus-benchmark` Spec Kit feature context.
- [x] T002 Add 058 plan, research, data model, contract, quickstart, and tasks artifacts.
- [x] T003 Update `AGENTS.md` active Spec Kit pointer to 058.
- [x] T004 Update `README.md`, `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`, and `docs/11-target-testing-and-acceptance.md` for 058 boundaries and commands.

## Phase 2: Foundational Contracts

- [x] T005 Add quality corpus failure enum in `src/veracrawl/contracts/enums.py`.
- [x] T006 Add quality corpus contracts in `src/veracrawl/contracts/real_world_quality.py`.
- [x] T007 Export quality corpus contracts in `src/veracrawl/contracts/__init__.py`.
- [x] T008 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`.
- [x] T009 Add contract tests in `tests/contract/test_real_world_quality_contracts.py`.
- [x] T010 Add registry tests in `tests/contract/test_real_world_quality_contract_registry.py`.
- [x] T011 Add import-boundary tests in `tests/contract/test_real_world_quality_import_boundaries.py`.

## Phase 3: Runtime And Replay

- [x] T012 Implement quality corpus runtime in `src/veracrawl/benchmarks/real_world_quality.py`.
- [x] T013 Implement replay checks in `src/veracrawl/review_replay/real_world_quality.py`.
- [x] T014 Add runtime tests in `tests/unit/test_real_world_quality_runtime.py`.
- [x] T015 Add replay tests in `tests/unit/test_real_world_quality_replay.py`.

## Phase 4: CLI And Fixtures

- [x] T016 Add `veracrawl-real-quality-corpus` CLI in `src/veracrawl/cli/real_quality_corpus.py`.
- [x] T017 Register CLI entry point in `pyproject.toml`.
- [x] T018 Add success fixture in `tests/fixtures/real-world-quality-corpus`.
- [x] T019 Add negative fixture `tests/fixtures/real-world-quality-insufficient-targets`.
- [x] T020 Add negative fixture `tests/fixtures/real-world-quality-insufficient-origins`.
- [x] T021 Add negative fixture `tests/fixtures/real-world-quality-insufficient-patterns`.
- [x] T022 Add negative fixture `tests/fixtures/real-world-quality-target-drift`.
- [x] T023 Add negative fixture `tests/fixtures/real-world-quality-missing-replay`.
- [x] T024 Add integration fixture tests in `tests/integration/test_real_world_quality_fixtures.py`.

## Phase 5: Validation

- [x] T025 Run Spec Kit prerequisite check for 058.
- [x] T026 Run ruff.
- [x] T027 Run mypy.
- [x] T028 Run registry validation.
- [x] T029 Run focused 058 tests.
- [x] T030 Run live quality corpus CLI validation.
- [x] T031 Run full pytest.
- [x] T032 Run Docker-backed pytest.
- [x] T033 Record all validation outputs in this file.
- [x] T034 Verify no docs, code, CLI output, or tests claim JS/browser, deep crawl, field-level oracle, precision/recall, repair, or production-quality release completion.

## Validation Results

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  passed for `specs/058-expanded-real-world-corpus-benchmark` with
  `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, and
  `tasks.md` available.
- `uv run --python python3.12 --extra dev ruff check .`: all checks passed.
- `uv run --python python3.12 --extra dev mypy src tests`: success across 609
  source files.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate
  --format json`: registry validation returned `ok: true`, `errors: []`,
  `warnings: []`, and `target_area_count: 62`.
- Focused 058 pytest gate:
  `tests/contract/test_real_world_quality_contracts.py`,
  `tests/contract/test_real_world_quality_contract_registry.py`,
  `tests/contract/test_real_world_quality_import_boundaries.py`,
  `tests/unit/test_real_world_quality_runtime.py`,
  `tests/unit/test_real_world_quality_replay.py`, and
  `tests/integration/test_real_world_quality_fixtures.py` passed with
  `22 passed in 114.80s`.
- Live public quality corpus CLI gate:
  `uv run --python python3.12 --extra dev veracrawl-real-quality-corpus run
  tests/fixtures/real-world-quality-corpus --profile quality --out
  .veracrawl-real-runs/real-world-quality-corpus` returned `ok: true`,
  `completion_result: pass`, `operator_status:
  real_world_quality_completed`, `declared_target_count: 40`,
  `passing_target_count: 40`, `origin_count: 21`,
  `pattern_family_count: 12`, `artifact_count: 40`, and
  `replay_bundle_count: 40`; the quality report recorded no policy denied,
  network unavailable, drift, or replay-missing failures.
- Live corpus pattern coverage included 12 pattern families:
  `pattern:api-json`, `pattern:api-xml`, `pattern:canonical-redirect`,
  `pattern:detail`, `pattern:documentation`, `pattern:error-empty-safe`,
  `pattern:feed-sitemap-document`, `pattern:listing`, `pattern:pagination`,
  `pattern:sparse-page`, `pattern:static`, and `pattern:table`.
- Full non-Docker pytest gate:
  `uv run --python python3.12 --extra dev pytest` passed with `1080 passed,
  5 skipped in 171.35s`.
- Docker-backed pytest gate used the repository's established live gate
  environment flags, not a pytest `--docker` option:
  `VERACRAWL_POSTGRES_DOCKER=1 VERACRAWL_REDIS_DOCKER=1
  VERACRAWL_S3_DOCKER=1 VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python
  python3.12 --extra dev --extra postgres --extra queue-redis --extra
  object-s3 pytest` passed with `1085 passed in 199.34s`.
- `uv run --python python3.12 --extra dev pytest --docker` was attempted while
  validating the original quickstart command and failed because this repository
  does not register a `--docker` pytest option. `quickstart.md` was corrected to
  the env-flag Docker-backed command above before marking T032 complete.
- Boundary check: `rg` confirmed 058-facing docs describe JS/browser quality,
  deep crawl quality, field-level oracles, precision/recall, repair success,
  and final production-quality release readiness as out of scope for this spec
  and assigned to specs 059-064 rather than claimed complete by 058.
