# Research: VeraCrawl Evidence and Publication Spine

## Decision: Build evidence from candidate field anchors, not from candidate values alone

- **Rationale**: Candidate values may be model-generated or heuristic. A source-backed
  anchor is the minimum replayable proof that a field can enter evidence coverage.
- **Alternatives considered**:
  - Accept candidate values as evidence: rejected because it violates the candidate-not-output boundary.
  - Require production object storage now: rejected because this slice proves contracts and gates through stable refs; storage adapters are later specs.

## Decision: Keep graph, memory, and agent reasoning refs out of source coverage

- **Rationale**: Graph and memory can explain planning or review routing, but they are
  not source evidence for publication. Agent reasoning is diagnostic only.
- **Alternatives considered**:
  - Allow graph/memory refs as coverage substitutes: rejected because target docs state graph and memory cannot replace source evidence.

## Decision: Publish through a report-first gate

- **Rationale**: Negative fixtures must return typed diagnostics without creating
  `PublishedOutput` or `OutputManifest`. A `PublicationReport` can represent both
  pass and fail outcomes while keeping output contracts immutable.
- **Alternatives considered**:
  - Raise exceptions for every gate failure: rejected because operator-visible and replay-visible failure reports are required.

## Decision: Deterministic fixture profile only

- **Rationale**: This spec validates target spine semantics before production
  persistence, review UI, export delivery, graph, and memory adapters exist.
- **Alternatives considered**:
  - Implement export/result delivery now: rejected because export and withdrawal are later dependency slices.
