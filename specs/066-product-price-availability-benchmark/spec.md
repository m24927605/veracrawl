# Feature Specification: US Top Ecommerce Product Price Availability Benchmark

**Feature Branch**: `066-product-price-availability-benchmark`  
**Created**: 2026-05-04  
**Status**: Planned  
**Input**: Test whether VeraCrawl can find a specified product on the United
States top ecommerce sites and extract price plus availability with evidence.

## Constitution Alignment

- **General-purpose crawler impact**: The benchmark defines reusable
  product-page price/availability extraction contracts and fixtures. It must not
  add Amazon-, Walmart-, or eBay-specific scraper modules, selectors, hidden
  endpoint assumptions, or bypass behavior.
- **Target/V1 boundary**: This is target architecture validation after rows 055,
  056, and 065. It probes product detail extraction on large ecommerce sites and
  records blocked sources honestly.
- **Evidence and replay impact**: Passing extracted fields require source
  anchors, artifact refs, content hashes, canonical URL refs, model/agent/tool
  traces, evidence/verification gate refs, command/event/outbox refs, and replay
  refs.
- **Safety and policy impact**: Robots preflight, origin allowlists,
  private-network denial, one product-page request per origin, no login/cart,
  no CAPTCHA/WAF bypass, and no LLM-as-evidence are mandatory.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`, `AGENTS.md`, `README.md`,
  `specs/055-*`, `specs/056-*`, and `specs/065-*`.

## User Scenarios & Testing

### User Story 1 - Extract Price And Availability Where Publicly Available (Priority: P1)

An operator gives a product identity and public product-page targets for major
United States ecommerce sites. VeraCrawl returns price and availability only
when both are source-backed.

**Independent Test**: Run `veracrawl-product-availability-benchmark run
tests/fixtures/us-top-ecommerce-product-availability --profile target --out
.veracrawl-real-runs/us-top-ecommerce-product-availability`.

**Acceptance Scenarios**:

1. **Given** an allowed product page with visible price and availability, **When**
   the benchmark runs, **Then** it returns normalized price, availability status,
   source anchors, artifacts, content hashes, AI traces, evidence refs, and replay
   refs.
2. **Given** a source denies access or hides price/availability, **When** the
   benchmark runs, **Then** the site result is blocked or needs review with typed
   diagnostics and no fabricated price or stock.

### User Story 2 - Verify Product Identity Before Field Acceptance (Priority: P1)

The extracted price/availability must belong to the specified product, not a
related accessory, sponsored item, refurbished variant, or wrong generation.

**Independent Test**: Contract/unit tests feed matching, wrong-product, missing
price, and missing availability HTML into the runtime.

**Acceptance Scenarios**:

1. **Given** the page contains the required identity terms, **When** price and
   availability are extracted, **Then** field outputs can pass.
2. **Given** the page misses required identity terms, **When** extraction runs,
   **Then** price and availability are rejected even if monetary strings exist.

### User Story 3 - Prove Hosted AI Decision Trace Participation (Priority: P2)

The benchmark can invoke a hosted OpenAI model through VeraCrawl's
framework-neutral model port to assist product identity, price candidate,
availability candidate, and verification decisions.

**Independent Test**: Run the CLI with `--model-provider openai` and inspect
`model_call_traces.json`, `agent_action_traces.json`, `tool_call_traces.json`,
and `context_bundle_traces.json`.

**Acceptance Scenarios**:

1. **Given** a product target with live evidence, **When** hosted OpenAI is
   selected, **Then** model call traces are recorded through `ModelProviderPort`.
2. **Given** model output recommends a value, **When** verification runs,
   **Then** the value is accepted only if source anchors and content hashes
   support it.

## Edge Cases

- Robots disallows a product URL: site result fails with robots-denied.
- Live HTTP returns access denied, anti-bot, or unavailable source page: site
  result is blocked with no extracted price/availability.
- Price appears in multiple places: choose the first source-backed candidate
  near product structured data or visible price markers, and record raw text.
- Availability is unknown or contradictory: return `unknown` or needs-review,
  not a guessed stock count.
- Currency is localized by the source response: preserve the observed currency
  instead of forcing USD.
- Hosted model is unavailable: record adapter failure in validation results; do
  not substitute a fake hosted-model pass.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define product price/availability benchmark contracts
  for manifest, target spec, field evidence, site result, and aggregate report.
- **FR-002**: System MUST support public product-page targets for Amazon,
  Walmart, and eBay under explicit origin allowlists and robots preflight.
- **FR-003**: System MUST extract normalized product identity match, price, and
  availability only from source-backed HTML artifacts.
- **FR-004**: System MUST include source anchor refs, artifact refs, content hash
  refs, canonical URL refs, evidence/verification refs, command/event/outbox
  refs, and replay refs for passing fields.
- **FR-005**: System MUST call model and agent ports for product identity,
  price candidate, availability candidate, and verification decisions for every
  live source with extractable evidence.
- **FR-006**: System MUST keep LLM output advisory; model output cannot be
  treated as source evidence or used to invent price/availability.
- **FR-007**: System MUST record blocked or access-denied targets honestly and
  allow the aggregate report to return `needs_review` when not all three sites
  are source-backed.
- **FR-008**: System MUST add CLI, fixtures/oracles, contract tests, runtime
  tests, integration tests, import-boundary tests, replay tests, registry
  validation, live runs, hosted OpenAI validation, full pytest, Docker-backed
  pytest, and task-log validation results.

### VeraCrawl Contract Requirements

- **VC-001**: The benchmark must remain general-purpose; target-specific data
  lives in fixture manifests, not code.
- **VC-002**: Runtime behavior must flow through existing live HTTP, model/agent
  ports, policy, command/event/outbox, evidence, and replay contracts.
- **VC-003**: Extracted price and availability are candidate field outputs gated
  by source evidence and verification; no real-site publication happens.
- **VC-004**: No login, cart, checkout, credential use, CAPTCHA solving, WAF
  evasion, stealth automation, proxy rotation, or robots bypass is allowed.
- **VC-005**: Every pass/fail/needs-review result must be typed and replayable.

### Key Entities

- **ProductAvailabilityBenchmarkManifest**: Declares product identity, public
  target specs, expected aggregate result, provider/framework requirements, and
  required refs.
- **ProductAvailabilityTargetSpec**: Declares one public product URL, robots URL,
  allowed origin, required product identity terms, and policy budgets.
- **ProductAvailabilityFieldEvidence**: Records one extracted field value with
  raw text, normalized value, source anchor, artifact/content hash, model/agent
  trace, evidence, verification, and replay refs.
- **ProductAvailabilitySiteResult**: Records per-site extracted fields or typed
  blocked/failure diagnostics.
- **ProductAvailabilityBenchmarkReport**: Aggregates per-site outcomes, AI trace
  refs, evidence refs, blocked source refs, and replay refs.

### Non-Goals

- This spec does not implement ecommerce search-result traversal or multi-page
  product discovery. The first benchmark uses declared public product-page
  targets for the specified product.
- This spec does not claim exact inventory counts unless the source page exposes
  them.
- This spec does not normalize regional delivery promises, tax, shipping,
  coupons, cart-only discounts, or personalized offers.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential
  theft, login-wall circumvention, WAF evasion, stealth automation,
  ban-avoidance proxy tactics, or bypassing robots, terms, or customer
  authorization policy.

## Success Criteria

- **SC-001**: Amazon and Walmart product pages produce source-backed price and
  availability results when live public HTML exposes those fields.
- **SC-002**: eBay access denial or source blocking is recorded as typed
  non-pass without fabricated price or inventory.
- **SC-003**: Hosted OpenAI validation records non-empty model, agent, tool, and
  context traces for extractable live targets.
- **SC-004**: Passing field evidence includes source anchor, artifact, content
  hash, evidence/verification, command/event/outbox, and replay refs.
- **SC-005**: All validation results are recorded in `tasks.md` with exact
  commands and actual pass/fail/needs-review status.

## Assumptions

- The benchmark uses SanDisk 256GB Extreme microSDXC UHS-I Memory Card with Adapter as the specified product because
  live preflight showed source-backed public product pages on Amazon and
  Walmart.
- Amazon may localize currency based on request geography; observed currency is
  preserved.
- eBay item pages may return `403 Access Denied` to the benchmark HTTP adapter;
  this is a valid outcome proving VeraCrawl does not bypass source controls.
