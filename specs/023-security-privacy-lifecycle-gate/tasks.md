# Tasks: VeraCrawl Security Privacy Lifecycle Gate

**Input**: Design documents from `specs/023-security-privacy-lifecycle-gate/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Phase 1: Setup

- [x] T001 Run Spec Kit prerequisite check for 023 feature context
- [x] T002 Add `veracrawl-security-privacy` CLI entry point in `pyproject.toml`

## Phase 2: Foundational Contracts

- [x] T003 Extend security/privacy enums in `src/veracrawl/contracts/enums.py`
- [x] T004 Add security/privacy contracts in `src/veracrawl/contracts/security_privacy.py`
- [x] T005 Export contracts in `src/veracrawl/contracts/__init__.py`
- [x] T006 Register contracts, commands, events, fixture oracles, and target area in `src/veracrawl/contracts/registry.py`
- [x] T007 Update registry expectations in `tests/contract/test_contract_registry.py`

## Phase 3: User Story 1 - Prove Security And Privacy Lifecycle Pass (P1)

- [x] T008 [P] [US1] Add contract tests in `tests/contract/test_security_privacy_contracts.py`
- [x] T009 [P] [US1] Add registry tests in `tests/contract/test_security_privacy_contract_registry.py`
- [x] T010 [P] [US1] Add fixture assertion helper in `tests/helpers/security_privacy_fixture_assertions.py`
- [x] T011 [US1] Implement gate runtime in `src/veracrawl/runtime_support/security_privacy.py`
- [x] T012 [US1] Implement CLI runner in `src/veracrawl/cli/security_privacy.py`
- [x] T013 [US1] Add `security-privacy-success` fixture/oracles
- [x] T014 [US1] Add success integration test

## Phase 4: User Story 2 - Reject Policy-Refs-Only Completion (P2)

- [x] T015 [P] [US2] Add import-boundary test
- [x] T016 [P] [US2] Add `security-privacy-policy-only` fixture/oracles
- [x] T017 [US2] Implement policy-only needs-review behavior
- [x] T018 [US2] Add policy-only integration coverage

## Phase 5: User Story 3 - Block Unsafe And Leaky Paths (P3)

- [x] T019 [P] [US3] Add negative fixture/oracles
- [x] T020 [P] [US3] Add negative unit tests
- [x] T021 [US3] Implement negative failure scenarios
- [x] T022 [US3] Add negative integration assertions

## Phase 6: Documentation And Acceptance

- [x] T023 Update README and docs/07, docs/09, docs/10, docs/11
- [x] T024 Update `AGENTS.md` active Spec Kit block for 023
- [x] T025 Run registry validation, ruff, mypy, focused tests, CLI fixtures, and full test suite
- [x] T026 Record real verification results in this `tasks.md`

## Review Record

- Review 1 - Contract completeness: found missing executable coverage for policy-only and negative security/privacy behavior; fixed by adding `SecurityPrivacyReport`, fixture manifest validation, CLI run report fields, and contract tests.
- Review 2 - Registry and target-area coverage: found target-area expectations needed to include `security_privacy_lifecycle_gate`; fixed registry tests and registered commands, events, fixture oracles, and target area.
- Review 3 - Coupling boundary: found 023 needed an explicit import-boundary test; fixed with runtime/CLI forbidden-import assertions for browser, model, agent framework, cloud, telemetry, vault, and security vendor SDKs.
- Review 4 - Fixture/oracle acceptance: found executable fixtures were missing for policy-only and eight negative cases; fixed with fixture manifests, security/privacy oracles, replay oracles, thresholds, unit tests, and integration assertions.
- Review 5 - Docs/spec alignment: found README/docs/07/09/10/11 and `AGENTS.md` needed 023 security/privacy lifecycle language; fixed with contract schema, implementation slice, fixture acceptance, CLI usage, and active Spec Kit plan updates.

## Validation Record

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` passed for `specs/023-security-privacy-lifecycle-gate`.
- `uv lock` resolved successfully.
- `uv run --python python3.12 --extra dev veracrawl-contracts validate` returned registry validation `ok: true`.
- `uv run --python python3.12 --extra dev veracrawl-security-privacy run ...` passed for all 10 security/privacy fixtures.
- `uv run --python python3.12 --extra dev ruff check src tests` passed.
- `uv run --python python3.12 --extra dev mypy src` passed: no issues in 172 source files.
- Focused 023 pytest passed: 20 passed.
- Full pytest without Docker passed: 420 passed, 5 skipped.
- Docker-backed full pytest passed: 423 passed, 2 skipped.
