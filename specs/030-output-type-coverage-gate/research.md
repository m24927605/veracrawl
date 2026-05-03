# Research: Target Output Type Coverage Gate

## Decision: Output Type Coverage Is A Publication Gate

Each target output type must prove source evidence, verification, publication, manifest, lifecycle, and replay refs before target coverage can pass.

**Rationale**: Target acceptance requires every output type to have evidence coverage and publication acceptance checks.

## Decision: Derived Context Is Diagnostic Only

Candidate, graph, memory, agent reasoning, and temporal KG refs can be present as diagnostics but cannot satisfy `source_evidence_refs`.

**Rationale**: This matches VeraCrawl's evidence boundary and prevents planning context from becoming publication truth.

## Decision: Type-Specific Refs Are Explicit

Tables require row/cell refs; documents require section/structure refs; files require hash/MIME/lifecycle refs; datasets require item evidence refs; facts require verification and temporal/canonical refs.

**Rationale**: Generic evidence coverage is not strong enough for target output readiness.

## Decision: Export Delivery Remains Out Of Scope

The gate proves output publication readiness before export. Export delivery and withdrawal stay in export connector specs.

**Rationale**: This keeps cohesion high and avoids coupling output coverage to external destinations.
