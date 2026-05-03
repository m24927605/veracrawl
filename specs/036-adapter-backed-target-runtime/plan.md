# Implementation Plan: VeraCrawl Adapter-Backed Target Runtime

**Branch**: `036-adapter-backed-target-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/036-adapter-backed-target-runtime/spec.md`

## Summary

Extend source-backed target runtime with adapter-backed acquisition proof. The core runner will accept canonical adapter-backed records and enforce adapter proof gates. CLI/adapters will materialize deterministic local source adapter records outside target runtime core. Reports will expose source adapter result refs and adapter output refs so source-backed target completion cannot rely on direct source reads alone.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12
**Primary Dependencies**: Pydantic; pytest/ruff/mypy for validation
**Storage**: Fixture files and generated run reports
**Testing**: Contract, unit, integration, CLI loop, registry validation, full pytest gates
**Performance Goal**: Adapter-backed target fixture loop completes within 60 seconds
**Constraints**: Target runtime core imports only standard library and VeraCrawl contracts; deterministic adapter materialization lives under `veracrawl.adapters.sources`

## Constitution Check

- [x] Target architecture capability is not reduced for schedule.
- [x] Core remains framework-neutral and adapter-neutral.
- [x] No single-site scraper logic is introduced.
- [x] Adapter-native state is not canonical.
- [x] Passing output requires evidence and replay refs.
- [x] Negative cases cannot be mislabeled complete.

## Project Structure

```text
specs/036-adapter-backed-target-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/adapter-backed-target-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/target_runtime.py
src/veracrawl/target_runtime/runner.py
src/veracrawl/cli/target_runtime.py
src/veracrawl/adapters/sources/target_runtime.py
tests/fixtures/adapter-backed-target-*/
tests/contract/test_adapter_backed_target_runtime_contracts.py
tests/unit/test_adapter_backed_target_runtime_runner.py
tests/integration/test_adapter_backed_target_runtime_fixtures.py
```

## Phase Plan

1. Define contracts and registry entries.
2. Materialize deterministic adapter-backed records outside core.
3. Enforce adapter-backed gates in target runtime runner.
4. Add fixtures, tests, and docs.
5. Run full validation and merge.

## Complexity Tracking

No constitution violation is expected. The implementation adds contracts because adapter-backed proof is a separate canonical concern from source corpus descriptors and source observations.
