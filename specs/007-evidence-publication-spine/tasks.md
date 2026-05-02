# Tasks: VeraCrawl Evidence and Publication Spine

**Input**: Design documents from `/specs/007-evidence-publication-spine/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. This feature implements field evidence coverage, evidence packets, verification/review decisions, publication gates, replay validation, fixtures, and import boundaries.

## Phase 1: Setup

- [X] T001 Add `veracrawl-evidence` console script target in `pyproject.toml`
- [X] T002 [P] Create evidence publication CLI module in `src/veracrawl/cli/evidence.py`
- [X] T003 [P] Extend evidence contracts in `src/veracrawl/contracts/evidence.py`
- [X] T004 [P] Extend verification contracts in `src/veracrawl/contracts/verification.py`
- [X] T005 [P] Extend publication contracts in `src/veracrawl/contracts/publication.py`
- [X] T006 [P] Create evidence coverage runtime in `src/veracrawl/evidence/coverage.py`
- [X] T007 [P] Create verification/review runtime in `src/veracrawl/verify/review.py`
- [X] T008 [P] Create publication gate runtime in `src/veracrawl/publish/gates.py`
- [X] T009 [P] Create publication replay validation in `src/veracrawl/review_replay/publication.py`
- [X] T010 [P] Create evidence fixture assertion helpers in `tests/helpers/evidence_fixture_assertions.py`

## Phase 2: Foundational

- [X] T011 [P] Write evidence publication registry tests in `tests/contract/test_evidence_publication_contract_registry.py`
- [X] T012 [P] Write evidence publication contract tests in `tests/contract/test_evidence_publication_contracts.py`
- [X] T013 [P] Write evidence publication import-boundary tests in `tests/contract/test_evidence_publication_import_boundaries.py`
- [X] T014 [P] Implement publication failure enums in `src/veracrawl/contracts/enums.py`
- [X] T015 Implement contract exports in `src/veracrawl/contracts/__init__.py`
- [X] T016 Extend registry for evidence publication contracts, commands, events, fixtures, and target area coverage in `src/veracrawl/contracts/registry.py`

## Phase 3: User Story 1 - Build Field Evidence Coverage (Priority: P1)

- [X] T017 [P] [US1] Write evidence coverage unit tests in `tests/unit/test_evidence_coverage.py`
- [X] T018 [P] [US1] Create `evidence-field-coverage` fixture manifests/oracles under `tests/fixtures/evidence-field-coverage/`
- [X] T019 [US1] Implement field evidence anchor and packet manifest building in `src/veracrawl/evidence/coverage.py`
- [X] T020 [US1] Implement fixture runner coverage-only success path in `src/veracrawl/cli/evidence.py`

## Phase 4: User Story 2 - Verify And Review Evidence Before Publication (Priority: P2)

- [X] T021 [P] [US2] Write verification/review unit tests in `tests/unit/test_verification_review.py`
- [X] T022 [P] [US2] Create `evidence-verification-review` fixture manifests/oracles under `tests/fixtures/evidence-verification-review/`
- [X] T023 [US2] Implement verification and review decisions in `src/veracrawl/verify/review.py`

## Phase 5: User Story 3 - Publish Only After Gates Pass (Priority: P3)

- [X] T024 [P] [US3] Write publication gate unit tests in `tests/unit/test_publication_gates.py`
- [X] T025 [P] [US3] Create `evidence-publication-success` fixture manifests/oracles under `tests/fixtures/evidence-publication-success/`
- [X] T026 [US3] Implement publication gate, output manifest, and publication report creation in `src/veracrawl/publish/gates.py`

## Phase 6: Negative Fixtures And Replay

- [X] T027 [P] Create negative evidence fixtures under `tests/fixtures/evidence-missing-anchor/`, `tests/fixtures/evidence-verification-conflict/`, `tests/fixtures/evidence-policy-denied/`, `tests/fixtures/evidence-replay-gap/`, and `tests/fixtures/evidence-candidate-direct-publication/`
- [X] T028 [P] Write publication replay tests in `tests/unit/test_publication_replay.py`
- [X] T029 [P] Write evidence publication fixture integration tests in `tests/integration/test_evidence_publication_fixtures.py`
- [X] T030 Implement typed failure handling for missing evidence, conflict, policy denial, replay gap, and direct candidate publication
- [X] T031 Implement publication replay validation in `src/veracrawl/review_replay/publication.py`

## Phase 7: Docs And Verification

- [X] T032 [P] Update evidence publication usage notes in `README.md`
- [X] T033 [P] Update evidence/publication package map and non-completion boundaries in `docs/10-target-implementation-design.md`
- [X] T034 [P] Update evidence publication fixtures and gates in `docs/11-target-testing-and-acceptance.md`
- [X] T035 Run `veracrawl-contracts validate --format json`
- [X] T036 Run evidence success and negative fixture CLI commands from `quickstart.md`
- [X] T037 Run ruff, mypy, and full pytest gate with a 30-second local timing check
- [X] T038 Run Spec Kit consistency checks equivalent to `$speckit-analyze` and record follow-up in this file
- [X] T039 Verify no code, docs, tests, CLI output, or task text claims graph/memory, export, distributed persistence, production browser rendering, or production scale readiness

## Implementation Verification Record

- Prerequisites: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/007-evidence-publication-spine`.
- Consistency review: 15 functional requirements, 7 success criteria, and T001-T039 are contiguous and mapped to contracts, tests, fixtures, docs, and verification gates. No clarification markers remain.
- Registry: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- CLI fixtures: `evidence-field-coverage`, `evidence-verification-review`, `evidence-publication-success`, `evidence-missing-anchor`, `evidence-verification-conflict`, `evidence-policy-denied`, `evidence-replay-gap`, and `evidence-candidate-direct-publication` all passed their declared oracles through `veracrawl-evidence run`.
- Quality gate: `ruff check src tests`, `mypy src`, and full `pytest` passed; full suite result was `154 passed in 9.63s`.
- Non-completion boundary: README, target implementation design, target testing docs, spec, tasks, code, tests, and CLI output were checked to avoid claiming completed graph/memory, export, distributed persistence, production browser rendering, review UI, or production scale readiness.
