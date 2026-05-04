# Tasks: Authorized Source Access And Official API Runtime

## Implementation

- [x] T001 Define authorized source access contract with credential grant,
  audit, redacted artifact, source anchor, content hash, policy, command/event,
  outbox, and replay refs.
- [x] T002 Register authorized source command/event coverage.
- [x] T003 Implement official API and credentialed-session access records in
  the shared runtime.
- [x] T004 Add authorized source fixture/oracle corpus.
- [x] T005 Add tests for redacted source evidence and replay refs.
- [x] T006 Add live official API evidence runner for authorized-source lower
  gate reports.
- [x] T007 Run live public official API validation and record the result.

## Validation Results

- Focused production-grade tests passed.
- Focused ruff passed.
- Full-suite validation is recorded in spec 075 after aggregate execution.

## Live Evidence Results: 2026-05-04

- Implemented `veracrawl-authorized-source run-live` for live public official
  API evidence. The runner fetches official API responses through a
  standard-library adapter layer, denies private/non-global hosts, enforces an
  artifact size budget, redacts body previews, records raw content hashes,
  source anchors, credential audit refs, policy refs, command/event/outbox refs,
  and replay refs, and emits a `ProductionGateReport`.
- Added fixture
  `tests/fixtures/production-authorized-source-live-official-api` using PyPI
  official JSON API and npm registry official package-version API.
- First live run failed honestly because `https://registry.npmjs.org/react`
  exceeded the 768KB artifact budget. The corpus was adjusted to the narrower
  official endpoint `https://registry.npmjs.org/react/latest`; the budget guard
  remains intact.
- Passing live command:
  `uv run --python python3.12 --extra dev veracrawl-authorized-source run-live tests/fixtures/production-authorized-source-live-official-api --profile production --out .veracrawl-real-runs/production-grade-release-20260504-162133/production-gates/071-authorized-source-live-official-api`.
- Result:
  `completion_result=pass`, `operator_status=production_authorized_source_access_completed`,
  `source_fetch_count=2`, `redacted_artifact_count=2`,
  `release_blocker_count=0`.
- Focused live authorized-source tests passed:
  `uv run --python python3.12 --extra dev pytest tests/unit/test_authorized_source_live_runtime.py tests/contract/test_production_grade_contract_registry.py -q`.
- Focused ruff passed:
  `uv run --python python3.12 --extra dev ruff check src/veracrawl/benchmarks/authorized_source_live.py src/veracrawl/cli/production_grade.py tests/unit/test_authorized_source_live_runtime.py tests/contract/test_production_grade_contract_registry.py`.
- Focused mypy passed:
  `uv run --python python3.12 --extra dev mypy src/veracrawl/benchmarks/authorized_source_live.py src/veracrawl/cli/production_grade.py tests/unit/test_authorized_source_live_runtime.py`.
- Registry validation passed:
  `uv run --python python3.12 --extra dev veracrawl-contracts validate`.
- Full ruff passed:
  `uv run --python python3.12 --extra dev ruff check .`.
- Focused production-grade tests passed:
  `uv run --python python3.12 --extra dev pytest tests/unit/test_authorized_source_live_runtime.py tests/contract/test_production_grade_contract_registry.py tests/contract/test_production_grade_contracts.py tests/unit/test_production_grade_runtime.py tests/integration/test_production_grade_fixtures.py -q`
  returned 29 passing tests.
- Full mypy passed:
  `uv run --python python3.12 --extra dev mypy src tests` returned
  `Success: no issues found in 690 source files`.
- Full pytest passed:
  `uv run --python python3.12 --extra dev pytest -q`.
- Docker-backed focused infrastructure pytest passed:
  `VERACRAWL_INFRASTRUCTURE_DOCKER=1 uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 pytest tests/integration/test_operational_infrastructure_live.py -q`.
