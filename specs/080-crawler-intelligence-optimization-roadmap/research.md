# Research: Crawler Intelligence Optimization Roadmap

## Decision 1: Use A Roadmap Control Spec Before Implementation Specs

**Decision**: Create spec 080 as a finite optimization roadmap and specs 081-087
as planned implementation specs.

**Rationale**: Existing roadmap rules prevent ad hoc production specs. A control
spec keeps dependency order explicit while preserving the 069-075
production-grade closure structure.

**Alternatives considered**:

- Add one large implementation spec: rejected because frontier, DOM,
  extraction, dedupe, ranking, ops gates, and runtime wiring have different
  owner services and acceptance tests.
- Add ad hoc specs without roadmap amendment: rejected because it violates the
  current Spec Kit governance.

## Decision 2: Treat Optimization Signals As Advisory Until Owner Services Act

**Decision**: Scores, DOM rankings, dedupe clusters, confidence, ranking
features, graph signals, memory, and LLM outputs remain advisory unless consumed
by the owning scheduler, verifier, publisher, review router, or ops service
through typed commands/events.

**Rationale**: VeraCrawl's architecture requires low coupling, evidence-backed
publication, and owner-service mutation boundaries. Advisory signals can improve
decisions without becoming source evidence.

**Alternatives considered**:

- Let agents directly reprioritize or publish: rejected because it bypasses
  owner services and replay gates.
- Treat score confidence as verification confidence: rejected because graph,
  memory, ranking, or model signals cannot replace source evidence.

## Decision 3: Sequence By Data Dependency

**Decision**: Implement scoring first, then DOM intelligence, extraction
fallback/confidence, canonical dedupe/identity, ranking, and aggregate
optimization gates.

**Rationale**: Ranking depends on verified fields and dedupe. Dedupe depends on
canonicalization and content fingerprints. Extraction stability depends on DOM
understanding. Cost/recovery gates need all lower reports.

**Alternatives considered**:

- Implement ranking first: rejected because ranking quality is weak without
  verified extraction and dedupe.
- Implement learning-to-rank immediately: rejected because labels and privacy
  readiness are not guaranteed.

## Decision 4: Keep Safety Boundaries Unchanged

**Decision**: Optimization specs do not authorize CAPTCHA solving, login-wall
bypass, WAF evasion, stealth automation, proxy rotation, unauthorized
credentials, robots bypass, or fabricated evidence.

**Rationale**: Better crawling must come from planning, source-backed adapters,
authorized APIs/sessions, DOM understanding, dedupe, cache, and repair, not
unsafe access-control circumvention.

**Alternatives considered**:

- Add stealth/browser evasion as cost optimization: rejected as a direct policy
  violation.
- Infer missing fields for ranking: rejected because unsupported fields must
  remain absent or needs-review.
