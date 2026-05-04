# Feature Specification: Taiwan Top Ecommerce Product Price Availability Benchmark

**Feature Branch**: `067-taiwan-product-availability-benchmark`  
**Created**: 2026-05-04  
**Status**: Planned  
**Input**: User request: "Set eBay aside. Run the same experiment against Taiwan's top three ecommerce platforms."

## Constitution Alignment

- **General-purpose crawler impact**: Extends the reusable product availability
  benchmark to Taiwan ecommerce pages without adding site-specific scraper
  modules. Chinese/Taiwan price and availability signals must be handled as
  generic source-pattern support.
- **Target/V1 boundary**: Market-validation benchmark work after spec 066. This
  does not weaken target architecture or claim broad product search traversal.
- **Evidence and replay impact**: Product identity, price, and availability
  fields require source anchors, artifacts, content hashes, model/agent/tool/
  context traces, command/event/outbox refs, and replay refs before publication.
- **Safety and policy impact**: The run must respect robots, origin scope,
  private-network denial, no login, no cart/checkout, no CAPTCHA solving, and no
  WAF or anti-bot bypass.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`, `AGENTS.md`, `README.md`.

## User Scenarios & Testing

### User Story 1 - Taiwan Product Field Extraction (Priority: P1)

As a VeraCrawl evaluator, I can run a declared Taiwan ecommerce product corpus
and see which platforms provide source-backed product price and availability.

**Why this priority**: This directly answers whether VeraCrawl can perform the
same product-price/availability experiment in Taiwan.

**Independent Test**: Run the Taiwan product availability fixture and inspect
site results for Shopee Taiwan, momo, and PChome 24h.

**Acceptance Scenarios**:

1. **Given** a declared SanDisk 256GB Extreme microSDXC target on momo, **When**
   the benchmark runs, **Then** price and availability are extracted from source
   evidence and gated by AI traces and verification refs.
2. **Given** a declared SanDisk 256GB Extreme microSDXC target on PChome 24h,
   **When** the benchmark runs, **Then** price and availability are extracted
   from source evidence and gated by AI traces and verification refs.
3. **Given** a Shopee Taiwan product URL that returns only a JavaScript shell or
   a blocked product API, **When** the benchmark runs, **Then** VeraCrawl records
   a typed needs-review/source limitation without fabricating price or stock.

### User Story 2 - Taiwan Locale Signals (Priority: P2)

As an implementer, I need Taiwan ecommerce pages to support metadata such as
`product:price:amount`, `product:price:currency`, `product:availability`, and
Chinese availability labels without coupling the runtime to one site.

**Independent Test**: Unit tests pass for HTML meta tags and Chinese
availability phrases.

### User Story 3 - Honest Market Result Reporting (Priority: P3)

As an operator, I need the run report to distinguish successful extraction from
blocked or JavaScript-only sources.

**Independent Test**: The Taiwan fixture reports `needs_review` overall when at
least one top platform cannot provide source-backed product fields through the
allowed acquisition path.

### Edge Cases

- A source returns HTTP 200 but only a JavaScript application shell with no
  product identity or field evidence.
- A source exposes product price/availability through standard meta tags instead
  of JSON-LD.
- A Taiwan page uses `TWD`, `NT$`, `元`, or `$` near explicit Taiwan currency
  metadata.
- A page contains both generic action labels and explicit out-of-stock metadata;
  explicit metadata wins.
- Robots, challenge, API 403, missing identity, missing price, missing
  availability, missing traces, or missing replay must fail or return
  `needs_review` visibly.

## Requirements

### Functional Requirements

- **FR-001**: System MUST add a Taiwan product availability fixture covering
  Shopee Taiwan, momo, and PChome 24h for a specified SanDisk 256GB Extreme
  microSDXC product family.
- **FR-002**: System MUST support source-backed price extraction from JSON-LD and
  OpenGraph/product meta tags, including Taiwan currency metadata.
- **FR-003**: System MUST support source-backed availability extraction from
  JSON-LD, product meta tags, and generic Chinese availability labels.
- **FR-004**: System MUST continue to use VeraCrawl model and agent abstraction
  ports for product identity, price candidate, availability candidate, and
  verification decisions.
- **FR-005**: System MUST NOT use LLM output as source evidence.
- **FR-006**: System MUST record Shopee Taiwan as non-pass if the allowed live
  HTTP/API path does not expose source-backed product fields.
- **FR-007**: System MUST write actual validation and live experiment results to
  `tasks.md`.

### VeraCrawl Contract Requirements

- **VC-001**: Preserve general-purpose crawling; no single-site parser module or
  platform-native SDK coupling may be introduced.
- **VC-002**: Product availability site results must retain policy, command,
  event, outbox, artifact, trace, and replay refs.
- **VC-003**: Field evidence must bind to source anchors/artifacts/content hashes.
- **VC-004**: Publication must remain gated by evidence and verification refs.
- **VC-005**: Fixtures, oracles, focused tests, live runs, and negative source
  outcomes must be recorded before merge.

### Key Entities

- **Taiwan Product Availability Fixture**: Declares product identity and three
  Taiwan ecommerce targets.
- **Product Availability Field Evidence**: Reuses the spec 066 contract for
  identity, price, and availability fields.
- **Product Availability Site Result**: Records pass or needs-review per
  platform with typed failure details.

### Non-Goals

- Do not implement Shopee CAPTCHA solving, product API bypass, stealth browser
  automation, login, cart, checkout, proxy evasion, or bot challenge evasion.
- Do not claim full Taiwan ecommerce production readiness from one product
  fixture.
- Do not implement category search traversal; this spec uses declared public
  target URLs.

## Success Criteria

- **SC-001**: Taiwan fixture runs against three public platform targets and
  writes source-backed site results.
- **SC-002**: At least momo and PChome produce price and availability evidence
  with model/agent/tool/context traces.
- **SC-003**: Shopee Taiwan non-pass outcome is recorded honestly without
  fabricated fields.
- **SC-004**: Registry validation, focused tests, full pytest, and live local and
  hosted OpenAI runs are recorded in `tasks.md`.

## Assumptions

- Taiwan top ecommerce platforms for this benchmark are Shopee Taiwan, momo, and
  PChome 24h, based on current public platform/traffic rankings and prior project
  roadmap row 065.
- The selected product family is SanDisk 256GB Extreme microSDXC because it has
  public targets on all three platforms.
- Public website content may drift during validation; drift must be reported,
  not hidden.
