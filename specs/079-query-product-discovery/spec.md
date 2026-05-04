# Feature Specification: Query Product Discovery And Offer Ranking

**Feature Branch**: `079-query-product-discovery`
**Created**: 2026-05-04
**Status**: Planned
**Roadmap Row**: 079
**Input**: The user challenged the prior iPhone 17 256G answer because VeraCrawl
was given product URLs manually. This spec closes that gap by requiring
query-driven discovery before product extraction and offer ranking.

## Constitution Alignment

- **General-purpose crawler impact**: Adds reusable query/search-result
  discovery contracts, candidate URL extraction, identity filtering, and offer
  ranking composition. Platform-specific source URLs live in manifests; runtime
  code must remain generic and must not become a Taiwan ecommerce scraper.
- **Target/V1 boundary**: Target architecture ecommerce validation layered on
  specs 066, 067, and 078. It does not weaken the production-grade crawler
  claim rules in specs 068-075.
- **Evidence and replay impact**: Search/listing pages, discovered candidate
  URLs, derived product targets, product field evidence, offer projection,
  model/agent/tool/context traces, command/event/outbox refs, and replay refs
  must be materialized. LLM output cannot be source evidence.
- **Safety and policy impact**: Robots preflight, origin allowlists,
  private-network denial, read-only acquisition, no login/cart/checkout,
  no CAPTCHA/WAF bypass, and no stealth/proxy tactics remain mandatory.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`, `AGENTS.md`, and `README.md`.

## User Scenarios & Testing

### User Story 1 - Discover Product Candidates From A Query (Priority: P1)

An operator provides a natural-language product query, allowed ecommerce search
entry points, and required product identity terms. VeraCrawl must fetch the
search/listing pages, extract candidate product URLs from source-backed
artifacts, and derive product availability targets without manually supplied
product URLs.

**Why this priority**: This is the exact gap identified by the user.

**Independent Test**: A fixture supplies only search URLs and local search-page
HTML. The runtime must discover candidate product URLs, prove source anchors and
AI traces, then build a derived product availability manifest.

**Acceptance Scenarios**:

1. **Given** a manifest with query `iphone 17 256G` and ecommerce search entry
   pages only, **When** discovery runs, **Then** discovered product candidates
   are emitted from search artifacts and no product target URL exists in the
   input manifest.
2. **Given** a search page with duplicate, off-origin, JavaScript, cart,
   compare, category, or account links, **When** discovery runs, **Then** only
   in-scope product-like candidate URLs are retained.

### User Story 2 - Compose Discovery With Product Extraction (Priority: P1)

The discovered candidate URLs are fed into the existing product availability
runtime so prices, inventory, delivery ETA, shipping fee, and offer records are
accepted only when source-backed.

**Why this priority**: Discovery alone does not answer ecommerce comparison
questions; it must compose with extraction and sorting.

**Independent Test**: A fixture search page discovers two product URLs. Product
page fixtures then produce source-backed price, availability, delivery ETA, and
shipping fee. The final offer projection must be sortable.

**Acceptance Scenarios**:

1. **Given** discovered product candidates that pass identity and field gates,
   **When** product extraction runs, **Then** price/availability/ETA/shipping
   evidence and sorted offer records are produced.
2. **Given** a discovered candidate is a wrong product, accessory, plan price,
   or blocked source, **When** extraction runs, **Then** the candidate remains
   typed non-pass and is not fabricated into the final ranking.

### User Story 3 - Return Ranked Answers With Evidence (Priority: P2)

For ecommerce comparison use, the runtime can materialize ranked answers by
item price, total price, delivery ETA, and availability from source-backed offer
records.

**Why this priority**: The user wants downstream website sorting by price,
arrival time, and inventory.

**Independent Test**: The CLI writes `ranked_offers.json` derived from
`ProductOfferProjectionReport.sorted_by_price_refs` and each offer's evidence
refs.

**Acceptance Scenarios**:

1. **Given** at least ten source-backed discovered offers, **When** ranking is
   requested, **Then** the first ten offers are ordered by price low-to-high and
   same-price delivery fast-to-slow.
2. **Given** fewer than ten source-backed offers, **When** the run completes,
   **Then** VeraCrawl reports the actual count and visible blocked/needs-review
   reasons instead of inventing missing answers.

### Edge Cases

- Search pages expose product URLs only in scripts or JSON payloads rather than
  anchor tags.
- Search pages include comparison, promo, cart, login, category, ad, or
  off-origin links.
- Search pages return JavaScript app shells with no source-backed candidate
  links.
- Candidate product pages contain navigation text for other products; identity
  checks must prefer product-title/metadata text where available and avoid
  rejecting or accepting based only on unrelated page chrome.
- Search or product acquisition is blocked by robots, WAF, login wall, or
  human-check pages.
- Required command, event, artifact, trace, policy, or replay refs are missing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define query product discovery contracts for source
  specs, discovered candidates, aggregate discovery report, and discovery
  benchmark manifest.
- **FR-002**: System MUST reject implementation paths that require manually
  supplied product target URLs in the discovery manifest.
- **FR-003**: System MUST fetch only manifest-declared search/listing entry
  URLs under robots preflight and origin allowlists before deriving product
  target URLs.
- **FR-004**: System MUST discover product-like candidate URLs from source-backed
  HTML anchors and structured script/text URL patterns, normalize relative URLs,
  dedupe, rank, and bound candidates per source and per run.
- **FR-005**: System MUST emit model call traces, agent action traces, tool call
  traces, context bundle traces, policy refs, command/event/outbox refs, source
  anchor refs, artifact refs, content hash refs, and replay refs for accepted
  discovered candidates.
- **FR-006**: System MUST compose discovered candidates into a derived
  `ProductAvailabilityBenchmarkManifest` and run the existing product
  availability and offer projection pipeline.
- **FR-007**: System MUST keep LLM output advisory; product URLs, prices,
  inventory, delivery ETA, and shipping fees must come from source artifacts.
- **FR-008**: System MUST improve product identity matching so rejected variant
  terms such as `Pro` or `17e` are evaluated against product identity text when
  available, not unrelated navigation chrome.
- **FR-009**: System MUST add CLI artifacts for discovery report, discovered
  candidates, derived product availability manifest, site results, field
  evidence, offer records, offer projection report, and ranked offers.
- **FR-010**: System MUST add contract, runtime, CLI, fixture/oracle,
  negative, replay, import-boundary, registry, and focused integration tests.

### VeraCrawl Contract Requirements

- **VC-001**: Preserve general-purpose AI agent crawling; platform-specific
  search entry URLs and URL patterns belong to manifests, not runtime modules.
- **VC-002**: Define owner services, commands, events, typed results, policy
  decisions, and replay refs for query discovery.
- **VC-003**: Candidate URLs are not facts; they become product targets only
  after source-backed discovery refs and later product evidence/verification
  gates.
- **VC-004**: No login, cart, checkout, credential use, CAPTCHA solving, WAF
  evasion, stealth automation, proxy rotation, or robots bypass is allowed.
- **VC-005**: Fixtures, oracles, negative tests, replay checks, and live
  validation results must be recorded before merge.

### Key Entities

- **ProductDiscoverySourceSpec**: One allowed search/listing entry point with
  query context, robots URL, origin scope, candidate URL patterns, and budgets.
- **ProductDiscoveryCandidate**: One source-backed discovered candidate URL with
  anchor/script context, trace refs, artifact/content hash refs, policy refs,
  command/event/outbox refs, and replay refs.
- **ProductDiscoveryRunReport**: Aggregate discovery and composition report with
  candidate refs, derived product availability report refs, offer projection
  refs, blocked source refs, and diagnostics.
- **ProductDiscoveryBenchmarkManifest**: Query-level fixture manifest declaring
  product identity, allowed search sources, candidate limits, provider/framework
  names, expected result, and required refs.

### Non-Goals

- This spec does not implement a global shopping search engine, paid search API,
  stealth browser automation, or crawling every result page indefinitely.
- This spec does not claim exact inventory counts or delivery promises unless
  the product source exposes them.
- This spec does not solve sources blocked by login walls, human checks, WAFs,
  or robots policy.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential
  theft, login-wall circumvention, WAF evasion, stealth automation,
  ban-avoidance proxy tactics, or bypassing robots, terms, or customer
  authorization policy.

## Success Criteria

- **SC-001**: A fixture with only search URLs discovers product candidates and
  produces a derived product availability manifest with no input product URLs.
- **SC-002**: Source-backed candidate records include artifact/content hash,
  source anchor, AI traces, policy, command/event/outbox, and replay refs.
- **SC-003**: Composed product availability results produce sorted offer records
  from discovered URLs.
- **SC-004**: Wrong variant/product candidates are blocked by identity gates and
  excluded from ranked offers.
- **SC-005**: The CLI can run a Taiwan query fixture for `iphone 17 256G` using
  public ecommerce search entry pages and writes honest source-backed or
  needs-review results.
- **SC-006**: Validation results in `tasks.md` include actual commands and
  pass/fail/needs-review outcomes for ruff, mypy, registry validation, focused
  tests, full pytest, Docker-backed pytest when available, and live query run.

## Assumptions

- Initial public query discovery supports read-only HTTP search/listing GET
  pages. Browser-rendered search discovery is a later extension unless search
  HTML is source-backed.
- Taiwan query validation can use PChome 24h and Yahoo Shopping search pages
  when their public HTML exposes product-like links; source-limited platforms
  remain needs-review.
- Product identity terms for `iphone 17 256G` are `iPhone`, `17`, and `256G`;
  variant exclusion terms can include `17e`, `Pro`, and `Pro Max` but must be
  evaluated against product identity text when available.
