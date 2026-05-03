# Implementation Plan: VeraCrawl Dynamic Source Adapter Runtime Foundation

**Branch**: `027-dynamic-source-adapter-runtime-foundation`
**Spec**: `specs/027-dynamic-source-adapter-runtime-foundation/spec.md`

## Summary

Implement a dynamic source runtime foundation that validates target source adapter families as runtime records, not just coverage descriptors. The core gate remains dependency-neutral; CLI dynamically loads adapter-owned deterministic/local builders. Non-fetch adapters emit native runtime refs instead of fake fetch/page semantics.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Pydantic, argparse, pytest, ruff, mypy
**Storage**: deterministic fixture run reports under `.veracrawl-test-runs/`
**Testing**: pytest contract/unit/integration, CLI fixture loop, registry validation, ruff, mypy, Docker-backed full suite
**Target Platform**: local deterministic source runtime foundation
**Project Type**: Python library/CLI
**Constraints**: no core static imports of browser/parser/vault/API/source runtime SDKs; no raw secret persistence; no adapter-native canonical state
**Canonical Contracts**: SourceAdapterResult, BrowserInteractionStep, CredentialUseAudit, DocumentArtifact, CommandResult, ObservabilityReport, SecurityPrivacyReport, DynamicSourceRuntimeAdapterRecord, DynamicSourceRuntimeReport

## Constitution Check

- General-purpose crawler scope preserved: no site-specific logic or source-specific hacks.
- Core remains dependency-neutral and imports only contracts for the gate.
- Missing live runtimes produce `needs_review`.
- Unsafe or incomplete mappings fail.
- Non-fetch adapters are native runtime records.

## Project Structure

```text
src/veracrawl/contracts/source_runtime.py
src/veracrawl/fetch/dynamic_source_runtime.py
src/veracrawl/adapters/sources/dynamic_runtime.py
src/veracrawl/cli/source_runtime.py
tests/contract/test_dynamic_source_runtime_contracts.py
tests/contract/test_dynamic_source_runtime_contract_registry.py
tests/contract/test_dynamic_source_runtime_import_boundaries.py
tests/unit/test_dynamic_source_runtime_gate.py
tests/integration/test_dynamic_source_runtime_fixtures.py
tests/fixtures/dynamic-source-runtime-*/
```

## Implementation Phases

1. Add contracts and failure enum.
2. Add core gate and adapter-owned deterministic/local builder.
3. Add CLI, registry entries, target area, fixtures, and tests.
4. Update docs and active Spec Kit pointer.
5. Run full verification and commit.

## Acceptance

- Registry validation passes.
- Focused dynamic source runtime tests pass.
- All CLI fixtures pass.
- Full non-Docker and Docker-backed suites pass.
