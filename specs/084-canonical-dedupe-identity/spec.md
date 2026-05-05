# Feature Specification: Canonical Dedupe And Identity Runtime

**Feature Branch**: `080-crawler-intelligence-optimization`  
**Created**: 2026-05-05  
**Status**: Implemented  
**Roadmap Row**: 084  
**Input**: Optimization roadmap requirement: improve URL canonicalization, duplicate suppression, near-duplicate detection, and entity/product/article identity handling.

## Summary

Build a canonical dedupe and identity runtime that normalizes URLs, suppresses
tracking/session/parameter explosions, clusters exact and near-duplicate pages,
separates template duplicates from content duplicates, and classifies same
product/article/page identities without merging distinct variants.

## Constitution Alignment

- **General-purpose crawler impact**: Dedupe and identity rules apply across
  URLs, pages, records, products, articles, documents, facts, and output
  manifests.
- **Target/V1 boundary**: Target architecture work layered on deep crawl,
  extraction quality, frontier scoring, and extractor fallback. V1 may use URL,
  redirect, canonical, page-structure, and template graph refs only.
- **Evidence and replay impact**: Dedupe and identity decisions preserve all raw
  observations and source evidence; suppression affects scheduling/publication
  routing, not artifact deletion.
- **Safety and policy impact**: Dedupe cannot fetch out-of-scope URLs, bypass
  robots, or use private data outside authorized policy.
- **Required reference docs**: `docs/02-production-architecture.md`,
  `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`,
  `docs/09-target-capability-model.md`, and
  `docs/10-target-implementation-design.md`.

## User Scenarios & Testing

### User Story 1 - Suppress URL And Content Duplicates (Priority: P1)

The crawler should avoid fetching or publishing duplicate URLs, pages, and
records caused by tracking parameters, sort parameters, redirects, canonicals,
and repeated templates.

**Why this priority**: Duplicate pollution wastes budget and corrupts coverage,
ranking, and review metrics.

**Independent Test**: Fixture URLs with UTM/session/sort/query variants,
redirects, canonical links, repeated listing templates, and duplicated details
produce suppression records and one canonical target.

**Acceptance Scenarios**:

1. **Given** URL variants with tracking parameters, **When** canonicalization
   runs, **Then** all variants map to a canonical URL and only allowed semantic
   parameters remain.
2. **Given** near-identical content with different URLs, **When** dedupe runs,
   **Then** exact hash, SimHash, or MinHash clusters explain suppression or
   review routing.

### User Story 2 - Preserve Real Variants (Priority: P1)

The crawler must distinguish same product/article/page duplicates from true
variants such as size, color, seller, language, date, document version, or SKU.

**Why this priority**: Over-aggressive dedupe loses recall and can rank the
wrong offer or document.

**Independent Test**: Product variants, article updates, localized pages, and
seller-specific offers are clustered or split according to identity rules and
source evidence.

**Acceptance Scenarios**:

1. **Given** same product with different colors or sellers, **When** identity
   projection runs, **Then** it preserves variant dimensions while linking the
   shared product identity.
2. **Given** same article reposted at multiple URLs, **When** identity
   projection runs, **Then** it clusters the article while preserving source URL
   evidence and canonical refs.

### Edge Cases

- Tracking parameters collide with semantic product or pagination parameters.
- Canonical links are missing, circular, cross-origin, or contradictory.
- Two pages share a template but have different entities.
- One product has multiple sellers, colors, storage sizes, or bundles.
- Localized pages share content but differ by language or region.
- Embedding similarity is high but source identity evidence is missing.
- Prior identity memory is stale after source drift.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define `CanonicalizationPolicy`,
  `CanonicalizationDecision`, `UrlParameterPolicy`,
  `DuplicateSuppressionRecord`, `ContentFingerprintRecord`,
  `NearDuplicateCluster`, `IdentityResolutionDecision`, and
  `VariantDimensionRecord` contracts.
- **FR-002**: System MUST normalize scheme/host casing, default ports, fragments,
  path dot segments, query parameter ordering, percent-encoding, trailing slash
  policy, redirects, and rel-canonical links.
- **FR-003**: System MUST remove known tracking/session parameters by default,
  including `utm_*`, `gclid`, `fbclid`, `msclkid`, `yclid`, `mc_cid`,
  `mc_eid`, `session`, `sid`, `phpsessid`, and configured equivalents.
- **FR-004**: System MUST preserve semantic parameters through allowlists for
  search, pagination, product identity, variant, language, date, and document
  version when configured by source/profile.
- **FR-005**: System MUST use exact content hash for exact duplicates,
  SimHash for near-duplicate page text, MinHash for listing/detail set overlap,
  and embedding similarity as advisory semantic dedupe where vector runtime is
  available.
- **FR-006**: System MUST classify duplicate type as url_variant,
  redirect_canonical, exact_content, near_duplicate, template_duplicate,
  same_entity, variant, language_variant, version_variant, or needs_review.
- **FR-007**: System MUST keep embedding and graph clusters advisory until
  current source evidence and identity rules confirm merge or split.
- **FR-008**: System MUST emit suppression, merge, split, and needs-review
  decisions with source refs, graph refs, policy refs, command/event/outbox
  refs, and replay refs.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST preserve general-purpose dedupe and identity logic
  without site-specific shortcuts in core.
- **VC-002**: System MUST define owner commands/events for canonicalization,
  suppression, merge, split, variant, and needs-review decisions.
- **VC-003**: System MUST preserve raw artifacts and evidence refs even when a
  duplicate is suppressed from fetching, review, ranking, or publication.
- **VC-004**: System MUST enforce source scope, robots, privacy lifecycle,
  retention, redaction, deletion, and legal-hold policies.
- **VC-005**: System MUST define duplicate, variant, negative, replay, and
  import-boundary tests before implementation.

### Key Entities

- **CanonicalizationPolicy**: Source/profile-specific parameter and URL
  normalization rules.
- **DuplicateSuppressionRecord**: Decision to suppress, retain, retry, or route
  a duplicate candidate.
- **ContentFingerprintRecord**: Exact hash, SimHash, MinHash, and optional
  embedding refs for a page or output.
- **IdentityResolutionDecision**: Merge/split/variant decision for pages,
  products, articles, documents, or records.

### Non-Goals

- This spec does not make embedding similarity authoritative evidence.
- This spec does not delete raw snapshots or historical evidence.
- This spec does not merge variants without source-backed identity evidence.
- VeraCrawl MUST NOT bypass robots, source access controls, or privacy
  lifecycle rules to improve dedupe.

## Success Criteria

- **SC-001**: Duplicate URL fetches decrease by at least 50% on parameter and
  redirect fixtures without losing required coverage.
- **SC-002**: Near-duplicate page clustering reaches at least 0.95 precision on
  fixture clusters and routes uncertain clusters to review.
- **SC-003**: Variant fixtures preserve distinct variant dimensions and do not
  collapse seller/color/size/language/version differences.
- **SC-004**: Every suppression or identity decision includes canonical URL,
  fingerprint, source refs, policy, command/event/outbox, and replay refs.
- **SC-005**: Negative fixtures fail for tracking parameter pollution,
  semantic parameter loss, embedding-only merge, missing canonical refs,
  duplicate publication, and missing replay.

## Assumptions

- Initial SimHash/MinHash implementations can be deterministic Python utilities
  behind graph/normalize owner services.
- Long-term cross-run identity improvement can use memory only after scoped
  retrieval and invalidation are available.

## Implementation Closure

- Materialized in `CanonicalizationDecision`, `ContentFingerprintRecord`,
  `IdentityResolutionDecision`, and `DuplicateSuppressionRecord`.
- Implemented deterministic URL canonicalization, tracking/session/sort
  parameter removal, stable SimHash/MinHash utilities, identity decisions, and
  duplicate suppression records.
- Validated by unit tests for canonicalization/fingerprints and fixture tests
  proving duplicate suppression refs and replay refs.
