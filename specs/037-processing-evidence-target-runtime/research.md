# Research: VeraCrawl Processing/Evidence Target Runtime Gate

## Decision 1: Processing/Evidence Proof Is Separate From Adapter Proof

**Decision**: Add `TargetProcessingEvidenceRecord` rather than overloading adapter-backed records.

**Rationale**: Adapter-backed records prove acquisition lineage. Processing/evidence records prove candidate, evidence, and publication lineage. Keeping these separate prevents adapter success from being mistaken for evidence success.

## Decision 2: Materialization Outside Core

**Decision**: Deterministic materialization lives in `veracrawl.adapters.sources.target_processing`.

**Rationale**: This preserves the core boundary while still proving executable behavior through CLI fixtures.

## Decision 3: Typed Failure Expansion

**Decision**: Add target runtime failure types for processing missing, evidence missing, publication bypass, and derived-context-as-evidence.

**Rationale**: These are distinct from missing source evidence and need precise operator diagnostics.
