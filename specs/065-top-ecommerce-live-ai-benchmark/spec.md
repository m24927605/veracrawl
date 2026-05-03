# Feature Specification: Top Ecommerce Live AI Benchmark

**Feature Branch**: `065-top-ecommerce-live-ai-benchmark`  
**Created**: 2026-05-04  
**Status**: Planned  
**Input**: Run experiments against three major Taiwan ecommerce sites and three
major United States ecommerce sites with live HTTP and framework-neutral AI
agent participation.

## Constitution Alignment

- **General-purpose crawler impact**: This adds a reusable corpus and benchmark
  acceptance path for large ecommerce homepages. It must not encode
  site-specific scraper logic, DOM selectors, hidden APIs, credentials, or
  anti-bot workarounds.
- **Target/V1 boundary**: This is target architecture validation that composes
  rows 055 and 056. It supplements the production quality roadmap; it does not
  weaken or replace specs 058-064.
- **Evidence and replay impact**: Passing runs require live HTTP refs,
  artifact/content hash/canonical refs, AI model call traces, agent action
  traces, tool call traces, context bundle traces, source anchors, extraction
  candidates, evidence/verification gate refs, command/event/outbox refs, and
  replay refs.
- **Safety and policy impact**: Robots preflight, origin allowlists,
  private-network denial, one homepage request per origin, and no bypass policy
  are mandatory. Blocked or drifted sources fail visibly.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/10-target-implementation-design.md`,
  `docs/11-target-testing-and-acceptance.md`, `AGENTS.md`, `README.md`,
  `specs/055-real-world-benchmark-corpus`, and
  `specs/056-real-world-ai-agent-crawl-planning-and-extraction-benchmark`.

## User Scenarios & Testing

### User Story 1 - Run Top Ecommerce Public Corpus (Priority: P1)

An operator can run a live public-corpus experiment against selected Taiwan and
United States ecommerce homepages and receive policy-gated observations.

**Why this priority**: The user's question is about real large ecommerce sites,
so the first proof must be live source acquisition rather than synthetic
fixtures.

**Independent Test**: Run `veracrawl-real-benchmark run
tests/fixtures/top-ecommerce-public-corpus --profile target --out
.veracrawl-real-runs/top-ecommerce-public-corpus`.

**Acceptance Scenarios**:

1. **Given** the six configured public ecommerce origins, **When** robots
   preflight and one homepage fetch pass, **Then** the corpus report passes with
   six observations and replay refs.
2. **Given** any target denies robots, drifts outside coarse oracle fragments,
   returns a non-HTML failure page, or exceeds policy/budget, **When** the run
   executes, **Then** the report fails with typed diagnostics instead of
   bypassing the site.

### User Story 2 - Prove AI Agent Participation (Priority: P1)

An operator can run the ecommerce corpus through the framework-neutral AI agent
benchmark and verify that a real hosted model participates in crawl planning,
site understanding, extraction candidate generation, and verification/repair.

**Why this priority**: The experiment must prove AI agent crawler capability,
not only policy-gated HTTP fetching.

**Independent Test**: Run `veracrawl-real-ai-benchmark run
tests/fixtures/top-ecommerce-ai-agent-corpus --profile target --model-provider
openai --out .veracrawl-real-runs/top-ecommerce-ai-agent-corpus-openai` with
`OPENAI_API_KEY` loaded from the operator environment or `~/.env`.

**Acceptance Scenarios**:

1. **Given** a passing public corpus run, **When** the OpenAI model provider
   adapter is selected, **Then** each of six sites records four AI decision
   traces and non-empty model/agent/tool/context trace files.
2. **Given** an extraction candidate generated from model/agent decisions,
   **When** the candidate is recorded, **Then** it is bound to source anchors,
   artifacts, and content hashes, and model output is not accepted as source
   evidence.

### User Story 3 - Document Ranking And Scope Limits (Priority: P2)

Maintainers can see which sites were selected, why the Taiwan ranking is not a
single official truth, and exactly what the experiment proves.

**Why this priority**: Ecommerce rankings vary by traffic, marketplace, GMV, and
local-platform definitions; the benchmark must be honest about its corpus.

**Independent Test**: Review spec, README, roadmap, and tasks validation notes
for the selected six sites, ranking caveats, live run outputs, and remaining
limits.

**Acceptance Scenarios**:

1. **Given** conflicting Taiwan ranking sources, **When** reading the benchmark
   documentation, **Then** the docs state that Shopee, momo, and PChome are the
   selected local ecommerce corpus while traffic-only rankings may show other
   third-place domains.
2. **Given** this homepage benchmark passes, **When** production readiness is
   discussed, **Then** the docs state that it proves policy-gated live + AI
   participation on large ecommerce entry points, not deep product/category
   extraction across the full sites.

## Edge Cases

- Robots deny the homepage or return an unexpected status: fail the site with
  `ROBOTS_DENIED`.
- The site returns an anti-automation, region, consent, or maintenance page:
  fail on observation mismatch instead of bypassing or hiding the drift.
- A target redirects outside the configured allowed origin: fail through source
  scope and canonical URL validation.
- The OpenAI adapter is unavailable, lacks credentials, or returns an API
  failure: fail or record the failed validation in `tasks.md`; do not replace it
  with a fake hosted-model pass.
- AI output suggests a candidate but no source anchor/artifact/content hash is
  present: fail publication/evidence acceptance.
- Core imports a concrete model SDK or agent framework: import-boundary tests
  fail.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define a `top-ecommerce-public-corpus` fixture with
  six public homepage targets: Shopee Taiwan, momo Shopping, PChome 24h,
  Amazon US, Walmart US, and eBay US.
- **FR-002**: System MUST define a `top-ecommerce-ai-agent-corpus` fixture that
  composes the public corpus with row 056 AI decision trace requirements.
- **FR-003**: Public corpus runs MUST use origin allowlists, robots preflight,
  private-network denial, content-type/body-size/coarse-fragment oracles, and
  one target request per site.
- **FR-004**: AI benchmark runs MUST execute crawl planning, site understanding,
  extraction candidate generation, and verification/repair for every passing
  site observation.
- **FR-005**: Hosted-model validation MUST use the existing model-provider port
  and OpenAI adapter, loading credentials from environment or `~/.env`.
- **FR-006**: Every passing AI decision MUST include model call trace, agent
  action trace, tool call trace, context bundle trace, policy refs,
  command/event/outbox refs, and replay refs.
- **FR-007**: Every extraction candidate MUST bind to source anchor refs,
  artifact refs, and content hash refs; LLM or agent output MUST NOT be source
  evidence.
- **FR-008**: The registry MUST register both new fixtures and keep the existing
  real-world benchmark and real-world AI contracts unchanged.
- **FR-009**: Validation results, including live HTTP and hosted OpenAI outputs,
  MUST be written back to `tasks.md` with exact commands and pass/fail status.

### VeraCrawl Contract Requirements

- **VC-001**: The benchmark must preserve general-purpose crawling and must not
  add site-specific extraction code, selectors, credentials, hidden endpoint
  assumptions, or scraper modules.
- **VC-002**: Owner-service behavior remains routed through existing live HTTP,
  real-world benchmark, agent/model port, command/event/outbox, and replay
  contracts.
- **VC-003**: This spec records evidence/verification gate readiness but does
  not directly publish ecommerce outputs.
- **VC-004**: Policy, credential, prompt-injection, privacy, retention, and
  export/withdrawal boundaries are inherited from rows 055 and 056.
- **VC-005**: Fixture/oracle tests, registry tests, live CLI runs, hosted LLM
  trace checks, ruff, mypy, focused tests, full pytest, Docker-backed pytest,
  and `git diff --check` are required before completion.

### Key Entities

- **Top Ecommerce Public Corpus Fixture**: A manifest-declared public homepage
  corpus with allowed origins, robots URLs, coarse content observations, rate
  budget refs, and replay requirements.
- **Top Ecommerce AI Agent Corpus Fixture**: A manifest that points to the
  public corpus and requires model, agent, tool, context, candidate, evidence
  gate, command/event/outbox, and replay refs.
- **Validation Run Output**: `run_report.json`, `summary.json`, trace JSON
  files, and task-log validation notes under `.veracrawl-real-runs/` and
  `specs/065-*/tasks.md`.

### Non-Goals

- This spec does not implement a full category or product deep crawl for the
  six ecommerce sites.
- This spec does not evaluate field-level precision/recall for real ecommerce
  product data.
- This spec does not attempt login, cart, checkout, account, personalization,
  CAPTCHA, WAF, consent bypass, proxy rotation, stealth automation, or
  anti-bot evasion.
- VeraCrawl MUST NOT implement CAPTCHA solving, paywall bypass, credential
  theft, login-wall circumvention, WAF evasion, stealth automation,
  ban-avoidance proxy tactics, or bypassing robots, terms, or customer
  authorization policy.

## Success Criteria

- **SC-001**: Live public corpus validation records six passing site
  observations or records exact typed failures in `tasks.md`.
- **SC-002**: Hosted OpenAI AI benchmark validation records at least 24 model
  call traces, 24 agent action traces, 24 tool call traces, 24 context bundle
  traces, and six extraction candidates for six passing sites.
- **SC-003**: Every passing extraction candidate has source anchor, artifact,
  content hash, evidence/verification gate, command/event/outbox, and replay
  refs.
- **SC-004**: Registry validation includes both top ecommerce fixtures.
- **SC-005**: Focused tests, full pytest, Docker-backed pytest, ruff, mypy, and
  `git diff --check` results are recorded honestly in `tasks.md`.

## Assumptions

- "Top three" is interpreted as a benchmark corpus of major ecommerce entry
  points rather than a legally authoritative ranking.
- United States corpus selection uses Amazon, Walmart, and eBay because current
  2026 ecommerce ranking sources consistently place them among the largest US
  ecommerce sites/marketplaces.
- Taiwan corpus selection uses Shopee Taiwan, momo Shopping, and PChome 24h to
  represent large local ecommerce platforms; traffic-only category sources may
  rank Taobao or Coupang in the third position depending on methodology.
- The experiment is a homepage/public-entry benchmark. Production claims beyond
  homepage live acquisition and AI decision traces require the broader quality
  specs and additional authorized corpora.
