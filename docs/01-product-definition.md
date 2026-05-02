# VeraCrawl Product Definition

## Name

Product name: VeraCrawl  
Full name: VeraCrawl AI Agent Web Crawler  
CLI name: `veracrawl`  
Internal short name: `vcrawl`

## One-line Positioning

VeraCrawl is being designed as a production-grade, general-purpose AI agent web crawler that understands websites, plans crawl strategies, adapts to page structure, extracts structured data, verifies evidence, remembers site behavior, and replays crawl decisions.

## Primary Goal

Build a general-purpose AI-native crawler that can accept high-level data objectives, propose crawl plans, and execute approved plans within explicit policy into controlled, observable, replayable crawl execution across many sites and data domains.

The crawler should use AI to maximize:

- website understanding
- crawl planning
- frontier prioritization
- page type classification
- schema and extraction planning
- selector and template adaptation
- evidence anchoring
- drift interpretation
- run repair
- long-term site learning

It must preserve:

- source evidence
- extraction provenance
- run replayability
- data freshness
- site and task memory
- operational observability
- scalable scheduling
- verifiable records, documents, datasets, and facts

## Non-goals

VeraCrawl is not:

- a single-site scraper
- a browser automation demo
- a pure vector database around crawled pages
- an untraceable extraction pipeline
- an LLM-only information extraction tool
- a vertical-only risk, compliance, ecommerce, or research product
- a mechanism for bypassing access controls or anti-abuse systems

## Product Principles

### 1. AI-Native Crawling

AI should be a first-class part of the crawler, not a post-processing add-on.

Agents should help VeraCrawl:

- understand the site objective
- infer likely page types and crawl paths
- choose source adapters
- prioritize frontier items
- propose extraction strategies
- recover from selector and template drift
- decide when more evidence is needed
- summarize failures and repair options
- reuse prior site and task memory

AI decisions must remain observable, bounded by policy, and replayable through explicit tool calls and events.

### 2. Evidence First

Every extracted value must be traceable back to:

- source URL
- crawl timestamp
- HTTP metadata
- content hash
- raw snapshot
- normalized text or DOM segment
- extractor version
- verification decision

The system may produce candidates quickly, but it should only publish verified outputs. Facts are one important output type, not the only output type.

### 3. Graph Native

Websites are graphs, not lists of pages. VeraCrawl should model:

- URL discovery graph
- hyperlink graph
- canonical and redirect graph
- page template graph
- entity relationship graph
- citation/source graph
- task dependency graph

Graph structure should influence agent planning, frontier scheduling, and quality checks. In V1, graph signals should not directly raise extraction or verification confidence; they may only affect discovery, prioritization, and review routing.

### 4. Memory Aware

AI agents should not restart from zero on every crawl run. VeraCrawl should preserve:

- site memories
- page type memories
- extraction memories
- error memories
- agent diaries
- temporal knowledge graph references derived from verified outputs
- reusable cross-site patterns

Memory is a planning, adaptation, and retrieval layer. Current evidence remains authoritative.

### 5. Replayable By Default

The platform must be able to answer:

- what user objective or instruction shaped the crawl
- which agent proposed the crawl strategy
- why a URL was discovered
- why a URL was prioritized
- which worker fetched it
- which extractor produced a value
- which evidence supported a published output
- why an output was rejected
- what changed between two runs
- which memories, graph signals, and evidence packets influenced an agent action

### 6. Production Before Convenience

Production-grade crawling requires:

- idempotent writes
- durable queues
- worker isolation
- retry and backoff
- state checkpoints
- schema versioning
- metrics and tracing
- cost controls
- data retention controls

These are not optional add-ons.

## High-level Product Surface

### User-facing Concepts

- Project: a business or research goal.
- Site: a crawlable source or domain.
- Objective: a user-defined crawling and extraction goal.
- Crawl plan: an AI-proposed execution strategy.
- Job: a configured crawl execution.
- Run: one execution of a job.
- Frontier: prioritized crawl task graph.
- Snapshot: raw captured source content.
- Site model: discovered page types, templates, paths, and graph structure.
- Extraction: candidate structured data.
- Evidence packet: source-backed support for a candidate.
- Published output: accepted record, document, dataset, or fact with provenance.
- Verified fact: accepted factual claim with provenance.
- Agent decision: replayable AI action with inputs, tool call, output, and reason.
- Memory: long-term agent/site/task knowledge.
- Report: canonical crawl outcome with quality notes.

### Main Interfaces

- Natural-language objective interface: describe what to crawl and extract.
- CLI: local and automation control.
- API: programmatic job and result access.
- Crawl console: operators, quality reviewers, and analysts.
- Agent tools: controlled tool surface for AI agents.
- Export connectors: database, warehouse, files, APIs.

## V1 Product Boundary

V1 should prove the general-purpose AI crawler loop without claiming arbitrary web mastery.

Primary V1 users:

- data engineers who need repeatable web extraction jobs
- AI platform engineers who need evidence-backed web data for downstream systems
- research or data operations analysts who review extracted outputs

Primary V1 buyer:

- head of data platform, AI platform, data operations, or engineering productivity

Buying trigger:

- existing scraper maintenance is too manual
- LLM extraction is not auditable enough
- teams need faster setup for new websites without losing replay, policy, and evidence controls

Supported V1 website patterns:

- static or mostly static HTML sites
- sitemap, RSS, and linked document collections
- listing/detail page structures
- pagination and canonical/redirect patterns
- pages that can be fetched through authorized HTTP or explicitly approved browser snapshots

Supported V1 objectives:

- discover relevant pages from seeds or sitemaps
- classify page types
- extract records, tables, document metadata, and factual fields against a declared schema
- build source evidence for each published output
- replay the crawl plan, agent actions, fetches, extraction decisions, and publication boundary

Explicit V1 non-support:

- arbitrary login flows without scoped customer-provided credentials
- adversarial access-control circumvention
- fully open-ended browsing without source scope
- automatic publication without verification policy
- claims of complete coverage for unfamiliar sites without benchmarked crawl reports
- dataset-scale exports, binary file workflows, and arbitrary document understanding beyond declared metadata

V1 success benchmark:

- a user objective can produce an approved crawl plan
- the run can fetch and normalize pages within policy
- the system can publish evidence-backed outputs for a declared schema
- every mutating or publication-relevant agent action is replayable
- operators can inspect the plan, evidence, policy decisions, and replay report without a full console product

V1 golden path:

```text
Create project and site
  -> define or approve schema
  -> describe crawl objective
  -> preview AI crawl plan and evidence requirements
  -> approve plan and policy decisions
  -> run crawl
  -> inspect candidates and evidence
  -> accept/reject/review outputs
  -> export accepted outputs
  -> inspect replay report
```

V1 schema workflow:

- user provides a declared schema or accepts an AI-proposed draft
- fields receive stable IDs, validators, and evidence requirements
- publication policy is approved before run execution
- schema changes require migration notes before comparing old and new outputs

V1 product success metrics:

- time to first approved crawl plan
- time to first evidence-backed published output
- schema setup time for a new site
- plan acceptance rate
- review time per output
- accepted output precision from reviewer decisions
- usable coverage for declared schema fields
- successful export delivery rate

V1 quickstart defaults:

- one project with one site and seed URL
- HTTP adapter enabled by default
- browser snapshots disabled until explicitly approved
- conservative public-web safety policy
- record/table/document-metadata schema templates
- source evidence required for every required field
- manual approval required before first publication
- local result materialization to JSON or Result API before production export connectors

V1 quickstart artifact:

```text
fixture: fixtures/sites/catalog-static
schema template: templates/schemas/basic-record.yaml
objective text: "Find listing and detail pages, extract the declared record fields, and keep evidence for each required field."
policy template: templates/policies/public-http-conservative.yaml
CLI entry: veracrawl init -> veracrawl plan -> veracrawl run -> veracrawl review -> veracrawl materialize
API entry: POST /objectives -> POST /plans/{id}/approve -> POST /runs -> GET /runs/{id}/review -> POST /exports
expected output: published record outputs, evidence coverage map, local JSON result materialization, replay report
```

V1 build brief:

- sample site: static documentation or catalog-style site with sitemap or listing/detail links
- sample schema: record with stable field IDs, required fields, optional fields, validators, and evidence requirements
- sample objective: find relevant pages, classify page types, extract declared records, and publish evidence-backed outputs
- acceptance case: one approved crawl plan, one completed run, at least one published output, evidence coverage map, export receipt, and replay report
- failure case: blocked source, policy-denied browser use, missing evidence, rejected candidate, and retryable fetch failure are visible to the operator
