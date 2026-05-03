# Implementation Plan: VeraCrawl Temporal KG Identity Projection Gate

**Branch**: `029-temporal-kg-identity-projection-gate` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/029-temporal-kg-identity-projection-gate/spec.md`

## Summary

Implement the executable temporal KG target gate that materializes authoritative entity identities, bitemporal projection records, identity adjudication records, runtime reports, CLI fixture validation, and deterministic positive/negative fixtures. The core remains graph-store-neutral and never lets temporal KG refs satisfy source evidence or publication requirements.

## Technical Context

**Language/Version**: Python 3.12 target with Python >=3.11 package support
**Primary Dependencies**: Pydantic v2, pytest, ruff, mypy
**Storage**: Deterministic in-memory contract objects and fixture reports only; no concrete graph store or persistence adapter in this slice
**Testing**: Unit, contract, integration fixture tests; `veracrawl-contracts validate`; CLI fixture loop; full pytest gates
**Target Platform**: Local deterministic CLI/runtime foundation
**Project Type**: Python package / CLI
**Performance Goals**: Deterministic temporal KG fixture loop under 30 seconds locally
**Constraints**: General-purpose crawler, low coupling/high cohesion, core independent of graph store, agent frameworks, model SDKs, storage, queues, browser runtimes, export targets, and site-specific scraper logic
**Scale/Scope**: Temporal KG identity/projection/adjudication contracts and fixture runtime gate; not production graph storage or graph explorer
**Canonical Contracts**: `TemporalKGEntityIdentity`, `TemporalKGProjectionRecord`, `TemporalKGIdentityAdjudicationRecord`, `TemporalKGRuntimeReport`, `TemporalKGFixtureManifest`
**Replay/Artifact Impact**: Pass reports require source verified fact refs, published output refs, source event refs, evidence packet refs, projection watermark refs, policy refs, command refs, event cursor refs, outbox refs, and replay bundle refs

## Constitution Check

- [x] General-purpose crawler capability preserved; no site-specific or vertical entity assumptions.
- [x] Target/V1 boundary explicit; this is target graph intelligence dependency sequencing, not a full production graph store claim.
- [x] Evidence and publication rules explicit; temporal KG never satisfies source evidence requirements.
- [x] Policy, command/event, outbox, replay, and no-runtime states are modeled.
- [x] Agent framework, model SDK, storage, queue, browser, graph store, and export target dependencies remain outside core.

## Project Structure

```text
src/veracrawl/contracts/enums.py
src/veracrawl/contracts/graph.py
src/veracrawl/contracts/__init__.py
src/veracrawl/contracts/registry.py
src/veracrawl/graph/temporal_kg.py
src/veracrawl/cli/temporal_kg.py
tests/contract/test_temporal_kg_contracts.py
tests/contract/test_temporal_kg_contract_registry.py
tests/contract/test_temporal_kg_import_boundaries.py
tests/unit/test_temporal_kg_gate.py
tests/helpers/temporal_kg_fixture_assertions.py
tests/integration/test_temporal_kg_fixtures.py
tests/fixtures/temporal-kg-*/
```

## Phase 0: Research And Design

See [research.md](research.md), [data-model.md](data-model.md), [contracts/temporal-kg-runtime.md](contracts/temporal-kg-runtime.md), [contracts/boundary.md](contracts/boundary.md), and [quickstart.md](quickstart.md).

## Phase 1: Contract And Registry

- Add temporal KG enums and Pydantic contracts.
- Export contracts from `veracrawl.contracts`.
- Register foundation contracts, commands, events, fixture oracles, and target area coverage.
- Add contract and registry tests before runtime behavior.

## Phase 2: Runtime Gate And CLI

- Implement deterministic temporal KG success, needs-review, and negative scenarios in `veracrawl.graph.temporal_kg`.
- Add `veracrawl-temporal-kg run` fixture CLI with manifest/oracle validation and `run_report.json` output.
- Add import-boundary tests to preserve dependency neutrality.

## Phase 3: Fixtures And Tests

- Add success fixtures for ordinary projection, false-merge adjudication, and false-split supersession.
- Add no-runtime and negative fixtures for target boundaries.
- Add helper assertions, unit tests, integration tests, CLI quickstart loop, registry validation, ruff, mypy, and full pytest.

## Complexity Tracking

No constitution deviations are required.

## Review Gates

- Requirements checklist must contain no placeholder or clarification markers.
- Tests must prove source evidence boundaries, provisional identity rejection, bitemporal required refs, false-merge/false-split adjudication behavior, and replay completeness.
- Docs and README must not claim production graph store, graph explorer, or publication-source-of-truth completion.
