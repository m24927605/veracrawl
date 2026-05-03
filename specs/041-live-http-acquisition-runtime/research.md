# Research: Live HTTP Acquisition Runtime

## Decision: Compose Existing Network Runtime With Production Spine

Use the existing network/source acquisition runtime for actual local HTTP
requests, and wrap it with row 039 run control plus row 040 persistence wiring.

**Rationale**: The repository already has adapter-owned standard-library HTTP,
network request/response contracts, source acquisition reports, and local
benchmark server fixtures. 041 should prove production integration instead of
duplicating that lower-level runtime.

## Decision: Source Observation As Acceptance Boundary

Create `TargetSourceObservationRecord` for passing HTTP responses so later
normalization and evidence specs can depend on a stable source-backed record.

**Rationale**: 045 and later specs need replayable source observations, not only
network response metadata.

## Rejected Alternative: Direct Fixture File Reads

Rejected because direct file reads would bypass the source adapter port and
would not prove live HTTP acquisition capability.
