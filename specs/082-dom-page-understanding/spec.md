# Feature Specification: DOM Page Understanding And Element Ranking Runtime

**Feature Branch**: `080-crawler-intelligence-optimization`  
**Created**: 2026-05-05  
**Status**: Implemented  
**Roadmap Row**: 082  
**Input**: Optimization roadmap requirement: improve DOM understanding, token efficiency, interactive element ranking, and page classification.

## Summary

Create a DOM intelligence runtime that treats DOM as the primary page
understanding surface, with screenshots reserved for browser evidence and visual
debugging. The runtime produces pruned DOM artifacts, page zone records,
interactive element rankings, repeated-block clusters, and LLM-ready context
bundles for search boxes, filters, pagination, sort controls, product cards,
price blocks, tables, and document metadata.

## Constitution Alignment

- **General-purpose crawler impact**: DOM intelligence supports many page
  patterns and schemas rather than a site-specific scraper.
- **Target/V1 boundary**: Target architecture work layered on live
  normalization and acquisition escalation. V1 may use static/mostly static DOM
  and approved browser snapshots only.
- **Evidence and replay impact**: DOM summaries and element rankings preserve
  source anchors and artifact refs, but do not replace evidence packets or
  verification decisions.
- **Safety and policy impact**: Browser interactions remain read-only and
  policy-gated; prompt-tainted content is labeled before model use.
- **Required reference docs**: `docs/02-production-architecture.md`,
  `docs/06-agent-system-design.md`, `docs/07-data-contracts.md`,
  `docs/09-target-capability-model.md`, and
  `docs/10-target-implementation-design.md`.

## User Scenarios & Testing

### User Story 1 - Produce LLM-Ready Pruned DOM Context (Priority: P1)

An agent needs compact page context without full DOM token waste or unsafe
prompt injection from untrusted content.

**Why this priority**: DOM pruning reduces model cost while preserving evidence
anchors and source structure.

**Independent Test**: A fixture page with nav, footer, listing cards, filters,
pagination, search, table, and article text produces a compact pruned DOM with
stable anchors and token-size limits.

**Acceptance Scenarios**:

1. **Given** a normalized or browser-rendered page, **When** DOM pruning runs,
   **Then** it emits pruned DOM nodes with role, tag, text excerpt, attributes,
   selector, visibility, source anchor, and taint metadata.
2. **Given** prompt-tainted page text, **When** the context bundle is built,
   **Then** untrusted content is labeled and cannot become tool instructions.

### User Story 2 - Rank Interactive Elements (Priority: P1)

The crawler needs to identify search boxes, filter controls, pagination, sort
buttons, document links, and product/detail links without clicking unsafe UI.

**Why this priority**: Better element ranking reduces useless browser steps and
improves discovery on unfamiliar websites.

**Independent Test**: Browser/DOM fixtures rank expected search, filter,
pagination, sort, and product-card links above login/cart/checkout/account
elements.

**Acceptance Scenarios**:

1. **Given** a page with many controls, **When** element ranking runs, **Then**
   read-only discovery controls are ranked with typed element roles and score
   explanations.
2. **Given** login, cart, checkout, account, destructive, or unknown controls,
   **When** ranking runs, **Then** they are blocked or marked unsafe with policy
   refs.

### Edge Cases

- DOM is empty because HTTP returned a JavaScript app shell.
- Browser DOM is available but includes a login wall, challenge, or human check.
- Repeated product cards have incomplete text or lazy-loaded images.
- Search/filter/pagination controls use ARIA labels but little visible text.
- The page contains prompt-injection text near candidate controls.
- DOM pruning removes a node required for evidence anchoring.
- Screenshot exists but DOM/source artifacts are missing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define `PrunedDomArtifact`,
  `DomNodeSummary`, `PageZoneClassification`, `RepeatedBlockCluster`,
  `InteractiveElementCandidate`, `ElementRankingScore`, and
  `DomContextBundle` contracts.
- **FR-002**: System MUST use DOM tree, normalized text, structured scripts,
  anchor maps, and browser DOM artifacts as primary understanding inputs;
  screenshot artifacts are diagnostic and evidence-preserving, not the primary
  parser.
- **FR-003**: System MUST identify page zones for navigation, footer, content,
  listing, detail, table, form, search, filters, pagination, sort, price,
  availability, document metadata, and repeated cards.
- **FR-004**: System MUST rank interactive elements with a default formula:

```text
element_score =
  0.30 * visibility +
  0.20 * label_intent_match +
  0.15 * semantic_role_match +
  0.15 * proximity_to_target_zone +
  0.10 * historical_success +
  0.10 * safe_readonly_action
  - 0.30 * unsafe_or_account_risk
  - 0.20 * prompt_taint_risk
```

- **FR-005**: System MUST classify search boxes, filters, pagination, sort
  controls, product cards, price blocks, availability blocks, table rows,
  document metadata, and API-like script payloads using deterministic
  heuristics first and LLM fallback only when confidence is below threshold.
- **FR-006**: System MUST bound DOM context size by node count, text bytes,
  repeated-block samples, and model-token budgets.
- **FR-007**: System MUST preserve source anchors, selector refs, raw artifact
  refs, content hashes, policy refs, command/event/outbox refs, and replay refs.
- **FR-008**: System MUST reject unsafe interactions including login, cart,
  checkout, mutation, account, credential entry, CAPTCHA, and challenge flows.

### VeraCrawl Contract Requirements

- **VC-001**: System MUST keep DOM intelligence generic across websites,
  languages, schemas, and output types.
- **VC-002**: System MUST define owner services, typed DOM artifacts, commands,
  events, policy decisions, and replay refs.
- **VC-003**: System MUST preserve source evidence boundaries; screenshots and
  DOM rankings cannot substitute for evidence packets when source anchors are
  required.
- **VC-004**: System MUST enforce prompt-injection, browser sandbox, credential,
  private-network, and read-only interaction policies.
- **VC-005**: System MUST define fixture/oracle, negative, replay, and
  import-boundary tests before implementation.

### Key Entities

- **PrunedDomArtifact**: Size-bounded DOM projection with taint labels and source
  anchors.
- **PageZoneClassification**: Typed zones and confidence/heuristic refs.
- **InteractiveElementCandidate**: Candidate element with role, safety class,
  selector, label, action type, evidence refs, and score.
- **DomContextBundle**: Agent-ready refs and summaries with redaction and
  prompt-taint policy.

### Non-Goals

- This spec does not implement arbitrary form submission.
- This spec does not permit destructive browser actions or credential entry.
- This spec does not use screenshots as the source of extracted facts when DOM
  or source artifacts are available.
- VeraCrawl MUST NOT implement CAPTCHA solving, login-wall bypass, WAF evasion,
  or stealth automation.

## Success Criteria

- **SC-001**: Pruned DOM context reduces model context bytes by at least 60% on
  DOM fixtures while retaining all oracle-required anchors.
- **SC-002**: Element role classification achieves at least 0.95 precision and
  0.90 recall on search, filter, pagination, sort, product card, and price
  block fixtures.
- **SC-003**: Unsafe element fixtures are blocked with policy refs and no
  browser mutation.
- **SC-004**: Every passing DOM artifact and element ranking includes artifact,
  anchor, policy, command/event/outbox, and replay refs.
- **SC-005**: Negative fixtures fail for missing anchors, prompt-taint bypass,
  unsafe interaction, oversized context, missing replay, and screenshot-only
  source evidence.

## Assumptions

- Initial DOM parsing may use existing normalized HTML/browser artifacts and
  standard parser capabilities behind owner services.
- Learned page-zone classifiers are future extensions; deterministic heuristics
  plus LLM fallback are sufficient for the first acceptance gate.

## Implementation Closure

- Materialized in `DomNodeSummary`, `PageZoneClassification`,
  `InteractiveElementCandidate`, and `DomContextBundle`.
- Implemented deterministic HTML-to-pruned-DOM context building, role/zone
  classification, and interactive element ranking in
  `src/veracrawl/benchmarks/crawler_optimization.py`.
- Validated by runtime and fixture tests requiring retained anchors, reduced
  DOM context, policy refs, command/event/outbox refs, and replay refs.
