# Research: Temporal KG Identity Projection Gate

## Decision: Temporal KG Is Authoritative Projection, Not Evidence

Temporal KG identities and projection records are derived projections. They may influence planning, review, contradiction detection, and repair, but publication evidence must still come from source artifacts, source anchors, evidence packets, and verified output refs.

**Rationale**: `docs/07-data-contracts.md` and `docs/11-target-testing-and-acceptance.md` explicitly state graph and temporal KG reads cannot satisfy publication evidence requirements.

## Decision: Require Bitemporal Refs

Projection records must carry valid-time refs and transaction-time refs. Identity records must include validity and transaction refs because identity state changes are facts about what VeraCrawl observed and when it projected or repaired that state.

**Rationale**: Target acceptance requires valid time, transaction time, supersession, conflict, invalidation, and projection watermark fields.

## Decision: Provisional Entity Clusters Cannot Enter Temporal KG

Entity clustering may produce graph hints, but an authoritative temporal KG identity requires identity evidence and canonical verified/published/event refs.

**Rationale**: This preserves the difference between exploratory site understanding and evidence-derived authoritative projection.

## Decision: False Merge And False Split Are Explicit Adjudication Paths

False merges must produce conflict/adjudication and invalidation or supersession refs. False splits must produce adjudication and supersession/resulting identity refs. Silent rewrites are forbidden.

**Rationale**: Operators and replay must be able to explain identity changes and recover prior state.

## Decision: Deterministic Runtime Gate Before Concrete Graph Store

This slice validates contracts, ownership, replay, and evidence boundaries with deterministic refs. Concrete graph store adapters and graph query APIs remain later work behind ports.

**Rationale**: The target architecture requires the semantic contract before choosing a graph storage implementation.
