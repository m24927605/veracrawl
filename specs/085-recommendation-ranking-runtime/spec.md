# Feature Specification: Recommendation Ranking Runtime

**Feature Branch**: `080-crawler-intelligence-optimization`  
**Created**: 2026-05-05  
**Status**: Implemented  
**Roadmap Row**: 085  
**Input**: Optimization roadmap requirement: improve recommendation and result ranking quality from evidence-backed outputs.

## Summary

Add a generic ranking runtime for source-backed results, offers, records,
documents, and facts. Ranking starts with explainable heuristic profiles and may
add learning-to-rank only after sufficient reviewer, click, or acceptance labels
exist. Ranking records must be deterministic, evidence-backed, explainable, and
must penalize stale, duplicate, source-limited, low-confidence, or missing-field
outputs without fabrication.

## Constitution Alignment

- **General-purpose crawler impact**: Ranking profiles apply to records,
  documents, facts, offers, freshness queues, review queues, and recrawl
  targets; ecommerce is a validation surface, not a product boundary.
- **Target/V1 boundary**: Target architecture work layered on offer projection,
  query discovery, extraction confidence, and dedupe/identity. V1 may use
  deterministic ranking for local/API results only when evidence gates pass.
- **Evidence and replay impact**: Ranking score records are output ordering
  metadata; they do not replace evidence, verification, or publication gates.
- **Safety and policy impact**: Ranking cannot infer restricted or missing
  source fields, expose private data, or hide blocked/source-limited sources.
- **Required reference docs**: `docs/01-product-definition.md`,
  `docs/02-production-architecture.md`, `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`, and
  `docs/10-target-implementation-design.md`.

## User Scenarios & Testing

### User Story 1 - Rank Evidence-Backed Outputs (Priority: P1)

Users need sorted outputs that match the objective and preserve why each item
ranked where it did.

**Why this priority**: Ranking is useful only after discovery, extraction, and
evidence gates produce enough candidates.

**Independent Test**: A fixture with accepted, stale, duplicate, partial,
source-limited, and high-confidence outputs emits ranking score records and
sorted refs.

**Acceptance Scenarios**:

1. **Given** evidence-backed records or offers, **When** ranking runs, **Then**
   each output gets a score breakdown and stable sorted position.
2. **Given** duplicate, stale, source-limited, or low-confidence outputs,
   **When** ranking runs, **Then** they are penalized or excluded according to
   profile policy.

### User Story 2 - Support Offer Ranking Without Fabrication (Priority: P1)

Product comparison outputs must rank by price, total price, availability,
delivery, source reliability, and evidence confidence while leaving missing
fields absent.

**Why this priority**: This extends specs 078 and 079 without making VeraCrawl
an ecommerce-only product.

**Independent Test**: Query-product discovery fixtures produce ranked offers by
price and total price, with blocked and missing delivery fields visible.

**Acceptance Scenarios**:

1. **Given** multiple product offers with source-backed price and availability,
   **When** offer ranking runs, **Then** lower total price and better
   availability rank higher within the selected profile.
2. **Given** missing delivery ETA or shipping fee, **When** total-price or
   delivery ranking runs, **Then** missing fields are marked unknown instead of
   inferred.

### Edge Cases

- Two offers have the same price but different evidence confidence or delivery.
- Required ranking fields are absent because source access is limited.
- Duplicate or variant outputs appear in the same top-k set.
- Reviewer labels are sparse, contradictory, private, or stale.
- A learning-to-rank model is configured without enough label quality.
- Ranking profile weights are malformed or unsupported for an output type.
- Ranked output refs lose publication or evidence refs after correction.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define `RankingProfile`, `RankingFeatureRecord`,
  `RankingScoreBreakdown`, `RankingDecision`, `RankedOutputSet`,
  `RankingEvaluationReport`, and `LearningToRankReadinessReport` contracts.
- **FR-002**: System MUST support ranking profiles for generic records,
  documents, facts, product offers, freshness queues, review queues, and
  recrawl targets.
- **FR-003**: System MUST use heuristic ranking first when no training labels
  exist and must block learning-to-rank activation until label count, label
  quality, privacy, drift, and replay readiness thresholds pass.
- **FR-004**: System MUST use this default generic ranking formula unless an
  approved profile overrides weights:

```text
rank_score =
  0.26 * intent_match +
  0.16 * evidence_quality +
  0.12 * extraction_confidence +
  0.10 * source_reliability +
  0.09 * freshness +
  0.08 * completeness +
  0.07 * availability_or_status +
  0.06 * cost_efficiency +
  0.06 * reviewer_or_label_signal
  - duplicate_penalty
  - source_limited_penalty
  - stale_or_low_confidence_penalty
```

- **FR-005**: System MUST use this default offer ranking formula for ecommerce
  validation profiles:

```text
offer_score =
  0.28 * intent_match +
  0.18 * availability_score +
  0.16 * price_score +
  0.12 * delivery_score +
  0.08 * seller_reputation +
  0.06 * rating +
  0.04 * review_count +
  0.04 * freshness +
  0.04 * extraction_confidence
  - penalties(source_limited, stale, low_evidence, duplicate, missing_required_field)
```

- **FR-006**: System MUST record source refs, evidence refs, verification refs,
  confidence refs, duplicate refs, policy refs, command/event/outbox refs, and
  replay refs for every passing ranking decision.
- **FR-007**: System MUST not infer missing price, shipping, delivery, rating,
  review count, availability, seller reputation, or freshness values unless
  source-backed evidence exists.
- **FR-008**: System MUST compute offline metrics including NDCG, MRR, precision
  at k, recall at k, source-limited rate, duplicate rate in top k, and
  unsupported-field rate where labels or oracles exist.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST keep ranking profiles output-type generic and avoid
  ecommerce-only assumptions in core ranking runtime.
- **VC-002**: System MUST define publish/ranking owner commands, events, score
  records, ranked refs, policy decisions, and replay refs.
- **VC-003**: System MUST preserve evidence and verification boundaries; ranking
  scores cannot publish, verify, or fabricate fields.
- **VC-004**: System MUST enforce privacy, label governance, source-limited
  visibility, correction, withdrawal, and replay behavior.
- **VC-005**: System MUST define ranking oracle, negative, replay,
  learning-to-rank readiness, and import-boundary tests before implementation.

### Key Entities

- **RankingProfile**: Target output type, features, weights, thresholds,
  missing-field policy, and sort keys.
- **RankingScoreBreakdown**: Per-output feature values, penalties,
  explanations, and final score.
- **RankedOutputSet**: Stable sorted refs and profile/version metadata.
- **LearningToRankReadinessReport**: Gate proving label and privacy readiness
  before any learned ranker is used.

### Non-Goals

- This spec does not train a ranker before sufficient labels exist.
- This spec does not fabricate unsupported fields for ranking.
- This spec does not make ranking score a verification decision.
- VeraCrawl MUST NOT use search snippets, model output, graph, or memory as
  substitute source evidence.

## Success Criteria

- **SC-001**: Ranking fixtures emit score breakdowns for 100% of ranked outputs.
- **SC-002**: Duplicate or source-limited outputs in top 10 decrease by at least
  30% compared with price-only or insertion-order baselines on ranking fixtures.
- **SC-003**: Offer ranking preserves source-backed sorted refs by price, total
  price, availability, and delivery while marking missing fields unknown.
- **SC-004**: Offline NDCG@10 or MRR improves against the heuristic baseline
  only when labels exist; otherwise the heuristic profile remains active.
- **SC-005**: Negative fixtures fail for missing evidence refs, fabricated
  fields, LLM-only ranking evidence, duplicate top-k pollution, missing replay,
  and premature learning-to-rank activation.

## Assumptions

- Reviewer decisions and accepted/rejected outputs are the initial label source.
- Learning-to-rank, if later enabled, must live behind ports/adapters and cannot
  persist framework-native state as canonical VeraCrawl state.

## Implementation Closure

- Materialized in `RankingProfile`, `RankingScoreBreakdown`,
  `RankedOutputSet`, and `RankingEvaluationReport`.
- Implemented evidence-backed heuristic ranking from intent match, price,
  availability, review count, rating, freshness, delivery, seller reputation,
  extraction confidence, and source reliability features.
- Validated by runtime and fixture tests requiring stable sorted refs, score
  breakdown refs, replay refs, and ranking-quality-regression failure handling.
