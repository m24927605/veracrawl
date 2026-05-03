# Research: VeraCrawl Adapter-Backed Target Runtime

## Decision 1: Adapter-Backed Proof Is A Contract Record

**Decision**: Add `TargetAdapterBackedSourceRecord` rather than overloading `TargetSourceObservationRecord`.

**Rationale**: Source observations describe content-derived evidence. Adapter-backed records describe acquisition lineage through `SourceAdapterResult` and adapter output refs. Keeping them separate preserves cohesion and makes direct source bypass detectable.

**Alternatives Considered**:

- Add ad hoc fields to source observations only. Rejected because missing adapter proof would be indistinguishable from missing source content.
- Execute concrete adapters inside target runtime core. Rejected because it violates the adapter-neutral core boundary.

## Decision 2: CLI/Adapter Layer Materializes Records

**Decision**: `veracrawl-target-runtime` loads deterministic local adapter materialization from `veracrawl.adapters.sources.target_runtime`, then passes canonical records into core.

**Rationale**: This proves executable adapter-backed behavior while keeping target runtime core free of concrete adapter imports.

**Alternatives Considered**:

- Hardcode adapter refs in runner. Rejected because that would be scaffold-like and would not prove the boundary.
- Use live network acquisition. Rejected for this spec because live external crawling and production network policy are separate target capabilities.

## Decision 3: Typed Failures Extend Target Runtime Failure Enum

**Decision**: Add `target_runtime_adapter_result_missing`, `target_runtime_adapter_output_mismatch`, and `target_runtime_direct_source_bypass`.

**Rationale**: Reusing `missing_evidence` or `false_complete` would hide distinct adapter proof failures and weaken reviewability.

## Decision 4: Existing Source-Backed Fixtures Remain Valid

**Decision**: Adapter-backed execution is opt-in through `adapter_backed_source_ref`.

**Rationale**: 034 deterministic and 035 source-backed fixtures must keep passing. Adapter-backed requirements apply only when a fixture declares the adapter backing manifest.
