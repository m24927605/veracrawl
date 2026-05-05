# Feature Specification: Extractor Fallback And Confidence Runtime

**Feature Branch**: `080-crawler-intelligence-optimization`  
**Created**: 2026-05-05  
**Status**: Implemented  
**Roadmap Row**: 083  
**Input**: Optimization roadmap requirement: improve extraction stability, JSON/schema consistency, field validation, confidence calibration, and abstention.

## Summary

Implement a deterministic-first extraction fallback chain and confidence runtime.
The system tries official or authorized sources, structured data, meta tags,
tables/repeated DOM blocks, selector memories, regex, and only then LLM
structured extraction. Every field candidate must carry anchors, validators,
confidence, extractor provenance, and abstention or review reasons when source
evidence is insufficient.

## Constitution Alignment

- **General-purpose crawler impact**: Extraction fallback is schema-driven and
  applies to records, tables, document metadata, facts, product offers, and
  other target output types.
- **Target/V1 boundary**: Target architecture work layered on normalization,
  schema extraction, evidence, and production quality gates. V1 remains declared
  schema first.
- **Evidence and replay impact**: Extractor attempts create candidates only;
  publication still requires evidence packets, verification decisions, output
  manifests, and replay.
- **Safety and policy impact**: LLM structured extraction uses sanitized context
  refs and cannot expose secrets or treat untrusted page content as tool
  instructions.
- **Required reference docs**: `docs/01-product-definition.md`,
  `docs/02-production-architecture.md`, `docs/06-agent-system-design.md`,
  `docs/07-data-contracts.md`, `docs/08-build-roadmap.md`,
  `docs/09-target-capability-model.md`, and
  `docs/10-target-implementation-design.md`.

## User Scenarios & Testing

### User Story 1 - Extract Through Deterministic Fallbacks (Priority: P1)

A schema-bound crawl should prefer stable source-backed extractors before LLM
structured extraction.

**Why this priority**: Deterministic extraction lowers cost and reduces
variance while keeping evidence anchors clear.

**Independent Test**: Field-oracle fixtures cover official API, JSON-LD,
OpenGraph/meta, table, repeated DOM cards, selector, regex, and LLM fallback
paths.

**Acceptance Scenarios**:

1. **Given** a page with schema.org product data, **When** extraction runs,
   **Then** JSON-LD fields are used before regex or LLM fallback.
2. **Given** visible repeated DOM cards but no structured data, **When**
   extraction runs, **Then** DOM-block extraction produces anchored candidate
   records.

### User Story 2 - Abstain Instead Of Publishing Weak Fields (Priority: P1)

When fields are missing, contradictory, stale, unanchored, or low confidence,
the system abstains or routes to review instead of publishing.

**Why this priority**: Source-backed abstention prevents false positives and
keeps reviewer queues honest.

**Independent Test**: Negative fixtures for wrong price, missing currency,
contradictory availability, stale evidence, and unanchored LLM output must
produce typed non-pass decisions.

**Acceptance Scenarios**:

1. **Given** conflicting price fields, **When** verification runs, **Then** it
   creates a conflict/review record rather than publishing.
2. **Given** LLM extraction returns JSON without evidence anchors, **When**
   evidence is built, **Then** the candidate is rejected.

### Edge Cases

- Multiple extractor attempts return conflicting values for the same field.
- Structured data exists but is stale, incomplete, or contradicts visible DOM.
- A field has a valid value but no resolvable source anchor.
- Price has amount but missing or ambiguous currency.
- Availability, date, delivery, or document metadata uses locale-specific text.
- Selector memory points to a changed template.
- LLM returns valid JSON shape but unsupported values or missing anchors.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define `ExtractorFallbackPlan`,
  `ExtractorAttemptRecord`, `FieldCandidateSet`, `FieldConfidenceScore`,
  `FieldValidationResult`, `ExtractorAbstentionDecision`, and
  `ExtractorDriftSignal` contracts.
- **FR-002**: System MUST execute extractor attempts in this default order:

```text
official_api_or_authorized_source
-> schema_org_json_ld_microdata_rdfa
-> opengraph_meta_product_tags
-> html_tables_and_repeated_dom_blocks
-> approved_selector_or_xpath_template
-> bounded_regex_with_validators
-> llm_structured_extraction_with_required_anchors
-> abstain_or_needs_review
```

- **FR-003**: System MUST require LLM structured extraction to output only the
  approved response schema with field IDs, values, normalized values,
  evidence-anchor refs, confidence, and abstention reasons.
- **FR-004**: System MUST validate price, currency, availability, title, URL,
  image URL, date/time, identity terms, delivery ETA, shipping fee, and document
  metadata through deterministic validators where applicable.
- **FR-005**: System MUST calculate field confidence from extractor reliability,
  anchor quality, validator pass rate, cross-source agreement, source
  reliability, freshness, template stability, and model uncertainty when used.
- **FR-006**: System MUST calibrate confidence against field-level oracle
  results and enforce publication thresholds by field criticality.
- **FR-007**: System MUST record extractor attempt order, skipped reasons,
  cost, latency, source refs, command/event/outbox refs, policy refs, and replay
  refs.
- **FR-008**: System MUST emit drift signals when selector failure, DOM cluster
  changes, field distribution shifts, or validator regressions exceed threshold.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST keep extraction strategy schema-driven and
  domain-general.
- **VC-002**: System MUST define extract/evidence/verify owner commands,
  events, typed attempt records, policy decisions, and replay refs.
- **VC-003**: System MUST preserve candidate/evidence/publication separation;
  extractor output cannot directly publish.
- **VC-004**: System MUST enforce prompt-taint, credential redaction, privacy,
  retention, and source evidence policies.
- **VC-005**: System MUST define field-oracle, negative, replay, confidence
  calibration, and import-boundary tests before implementation.

### Key Entities

- **ExtractorFallbackPlan**: Ordered extractor chain, allowed field types,
  thresholds, and fallback policy.
- **ExtractorAttemptRecord**: One extractor invocation with inputs, outputs,
  skip/failure reasons, anchors, cost, and replay refs.
- **FieldConfidenceScore**: Field-level score, calibration slice, feature values,
  and threshold result.
- **ExtractorAbstentionDecision**: Typed reason a field or record is not
  publishable.

### Non-Goals

- This spec does not allow LLM output to become source evidence.
- This spec does not auto-publish exploratory schema fields without approval.
- This spec does not replace evidence or verification services.
- VeraCrawl MUST NOT fabricate unavailable fields, prices, inventory, ratings,
  or document metadata.

## Success Criteria

- **SC-001**: Field oracle precision remains at least 0.98, recall at least
  0.90, F1 at least 0.94, and critical-field precision at least 0.99 on the
  extraction optimization corpus.
- **SC-002**: LLM extraction attempts are reduced by at least 40% on pages with
  structured data or stable DOM fields compared with LLM-first extraction.
- **SC-003**: Low-confidence or unanchored fields abstain with typed reasons and
  do not publish.
- **SC-004**: Every accepted field has source anchor, artifact, content hash,
  validator, evidence packet, verification, policy, command/event/outbox, and
  replay refs.
- **SC-005**: Negative fixtures fail for wrong value, missing anchor, stale
  evidence, contradictory evidence, schema violation, LLM-as-evidence, missing
  replay, and publication bypass.

## Assumptions

- Existing product availability extractor behavior can be generalized into
  schema-bound extractor attempts without hard-coding ecommerce-only logic.
- Selector memories remain advisory until current-run source anchors verify the
  extracted field.

## Implementation Closure

- Materialized in `ExtractorFallbackPlan`, `ExtractorAttemptRecord`,
  `FieldConfidenceScore`, and `ExtractorAbstentionDecision`.
- Implemented deterministic fallback ordering for JSON-LD, schema.org,
  OpenGraph, CSS selector, XPath, regex, and LLM structured fallback with
  confidence thresholding and abstention semantics.
- Validated by runtime and contract tests requiring source anchors, content
  hashes, validators, evidence packets, publication gates, and rejection of LLM
  output as accepted source evidence.
