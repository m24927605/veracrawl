# Research: VeraCrawl Basic Site Graph Spine

## Decision: Use deterministic in-memory graph records

- **Rationale**: This slice proves graph contracts, replay, and evidence boundaries
  before a production graph store adapter exists.
- **Alternatives considered**:
  - Add a graph database dependency now: rejected because concrete graph stores must
    enter through adapters in a later spec.

## Decision: Build graph from provenance refs, not scraped strings

- **Rationale**: Graph records must be reconstructable from link provenance,
  canonical/redirect refs, page type refs, and site model refs.
- **Alternatives considered**:
  - Build graph from ad hoc URLs in tests only: rejected because it would weaken
    replay and provenance semantics.

## Decision: Treat graph-as-evidence as a typed boundary violation

- **Rationale**: Target docs explicitly state graph signals cannot replace source
  evidence for publication.
- **Alternatives considered**:
  - Allow graph refs for low-risk fields: rejected because it creates an unsafe
    publication loophole.
