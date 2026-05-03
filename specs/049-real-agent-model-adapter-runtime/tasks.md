# Tasks: Real Agent And Model Adapter Runtime

**Input**: Design documents from `/specs/049-real-agent-model-adapter-runtime/`

## Phase 1: Contracts And Registry

- [x] T001 Add real agent/model adapter failure enum in `src/veracrawl/contracts/enums.py`
- [x] T002 Add runtime report and fixture manifest contracts in `src/veracrawl/contracts/agent_model_runtime.py`
- [x] T003 Export row 049 contracts in `src/veracrawl/contracts/__init__.py`
- [x] T004 Register contracts, commands, events, fixtures, and target area in `src/veracrawl/contracts/registry.py`
- [x] T005 [P] Add contract tests in `tests/contract/test_agent_model_adapter_runtime_contracts.py`
- [x] T006 [P] Add import-boundary tests in `tests/contract/test_agent_model_adapter_runtime_import_boundaries.py`

## Phase 2: Runtime, Adapters, And CLI

- [x] T007 Add core port-composed runtime in `src/veracrawl/agents/real_adapter_runtime.py`
- [x] T008 Add local model provider runtime adapter in `src/veracrawl/adapters/model_providers/local_runtime.py`
- [x] T009 Add external model provider runtime adapter wrapper in `src/veracrawl/adapters/model_providers/external_runtime.py`
- [x] T010 Add native agent runtime adapter in `src/veracrawl/adapters/agent_frameworks/native_runtime.py`
- [x] T011 Add external agent framework runtime adapter wrapper in `src/veracrawl/adapters/agent_frameworks/external_runtime.py`
- [x] T012 Add CLI in `src/veracrawl/cli/agent_model_runtime.py`
- [x] T013 Add `veracrawl-agent-model-runtime` entry point in `pyproject.toml`
- [x] T014 [P] Add runtime unit tests in `tests/unit/test_agent_model_adapter_runtime.py`
- [x] T015 [P] Add adapter unit tests in `tests/unit/test_agent_model_adapter_runtime_adapters.py`
- [x] T016 [P] Add integration tests in `tests/integration/test_agent_model_adapter_runtime_fixtures.py`

## Phase 3: Fixtures

- [x] T017 [P] Add local runtime success fixture
- [x] T018 [P] Add runtime unavailable fixture
- [x] T019 [P] Add missing run-control fixture
- [x] T020 [P] Add missing live-normalization fixture
- [x] T021 [P] Add missing schema-extraction fixture
- [x] T022 [P] Add unsupported provider fixture
- [x] T023 [P] Add unsupported framework fixture
- [x] T024 [P] Add raw prompt leak fixture
- [x] T025 [P] Add raw response leak fixture
- [x] T026 [P] Add raw credential leak fixture
- [x] T027 [P] Add framework-state-canonical fixture
- [x] T028 [P] Add provider-transcript-canonical fixture
- [x] T029 [P] Add missing model trace fixture
- [x] T030 [P] Add missing tool trace fixture
- [x] T031 [P] Add missing replay fixture
- [x] T032 [P] Add core import boundary fixture

## Phase 4: Docs

- [x] T033 [P] Update `README.md`
- [x] T034 [P] Update `docs/07-data-contracts.md`
- [x] T035 [P] Update `docs/08-build-roadmap.md`
- [x] T036 [P] Update `docs/10-target-implementation-design.md`
- [x] T037 [P] Update `docs/11-target-testing-and-acceptance.md`
- [x] T038 Update `AGENTS.md` active Spec Kit pointer

## Phase 5: Verification

- [x] T039 Run Spec Kit prerequisite check
- [x] T040 Run `uv lock`
- [x] T041 Run ruff
- [x] T042 Run mypy
- [x] T043 Run registry validation
- [x] T044 Run focused row 049 tests
- [x] T045 Run row 049 CLI fixture loop
- [x] T046 Run full non-Docker pytest gate
- [x] T047 Run Docker-backed pytest gate
- [x] T048 Run `git diff --check`
- [x] T049 Record validation results

## Validation Results

- Spec Kit prerequisite: passed for `specs/049-real-agent-model-adapter-runtime`.
- `uv lock`: resolved 30 packages.
- `ruff check .`: passed.
- Focused mypy: passed for `src`, row 049 contract/unit/integration tests, and registry tests; 247 source files checked.
- Registry validation: `ok=true`, no errors.
- Focused pytest: 51 passed.
- `veracrawl-agent-model-runtime` CLI loop: 16 fixtures passed.
- Full non-Docker pytest: 945 passed, 5 skipped.
- Docker-backed pytest: 950 passed.
- `git diff --check`: passed.
