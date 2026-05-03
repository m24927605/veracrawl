# Implementation Plan: VeraCrawl Processing/Evidence Target Runtime Gate

**Branch**: `037-processing-evidence-target-runtime` | **Date**: 2026-05-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/037-processing-evidence-target-runtime/spec.md`

## Summary

Extend adapter-backed target runtime with canonical processing/evidence/publication lineage. The CLI loads deterministic local materialization outside core and passes `TargetProcessingEvidenceRecord` objects into the runner. The runner gates completion on normalized document, extraction candidate, evidence packet, evidence anchor, publication report, policy, and replay refs.

## Technical Context

**Language/Version**: Python 3.11+ with tests run on Python 3.12
**Primary Dependencies**: Pydantic; pytest/ruff/mypy for validation
**Storage**: Fixture files and generated run reports
**Testing**: Contract, unit, integration, CLI loop, registry validation, full pytest gates
**Constraints**: Target runtime core imports only standard library and VeraCrawl contracts

## Constitution Check

- [x] Capability is not reduced for schedule.
- [x] Core remains framework-neutral and adapter-neutral.
- [x] No single-site scraper logic is introduced.
- [x] Source evidence remains required.
- [x] Negative cases cannot be mislabeled complete.

## Structure

```text
specs/037-processing-evidence-target-runtime/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/processing-evidence-target-runtime.md
├── quickstart.md
└── tasks.md

src/veracrawl/contracts/target_runtime.py
src/veracrawl/target_runtime/runner.py
src/veracrawl/cli/target_runtime.py
src/veracrawl/adapters/sources/target_processing.py
tests/fixtures/processing-evidence-target-*/
```
