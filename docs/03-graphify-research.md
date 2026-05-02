# Graphify Research Notes

Repository studied: `https://github.com/safishamsi/graphify`

## Core Takeaway

Graphify is useful for VeraCrawl because it treats knowledge extraction as a graph-building pipeline rather than a flat extraction task. For an AI agent crawler, this graph becomes an operational map that agents use to understand unfamiliar sites, plan exploration, prioritize work, avoid duplicate paths, and explain crawl decisions.

The most transferable pattern is:

```text
detect -> extract -> build -> cluster -> analyze -> report -> export
```

For a crawler, this becomes:

```text
discover -> fetch -> normalize -> graph-build -> cluster -> prioritize -> verify -> report
```

## What To Borrow

### 1. Structural Extraction Before Semantic Inference

Graphify separates raw structural extraction from later graph analysis. VeraCrawl should follow the same rule:

- collect URL links
- collect redirects
- collect canonical tags
- collect DOM sections
- collect entities
- collect page templates
- only then infer relationships or importance

This reduces hallucination risk and makes debugging easier.

### 2. Edge Type Discipline

Graphify-style graph systems benefit from explicit edge categories.

VeraCrawl should model URL and entity edges with typed relationships:

- `links_to`
- `redirects_to`
- `canonical_of`
- `contains_entity`
- `mentions_entity`
- `same_template_as`
- `parent_section_of`
- `pagination_next`
- `listing_contains_detail`
- `cites_source`
- `conflicts_with`
- `supports_fact`

Edge typing is what lets graph analysis become operationally useful.

### 3. Extracted / Inferred / Ambiguous Distinction

VeraCrawl should distinguish:

- Extracted: directly observed from source.
- Inferred: derived from graph or rules.
- Ambiguous: plausible but not publishable.

This distinction should appear in every candidate, evidence packet, and graph edge.

### 4. Clustering And Community Detection

Clustering can help crawler planning:

- detect site sections
- group page templates
- find orphan pages
- identify high-value hubs
- identify low-value duplicate zones
- detect topic communities
- prioritize bridge pages

Useful graph-derived crawl signals:

- hub score
- authority score
- bridge score
- duplicate cluster membership
- distance to seed
- distance to verified entity
- stale cluster score
- unresolved conflict cluster

### 5. Cache And Manifest Discipline

Graphify's pipeline mindset supports deterministic runs and reusable intermediate artifacts.

VeraCrawl should write manifests for:

- input seeds
- crawl scope
- fetch artifacts
- normalized documents
- graph build version
- extractor version
- verification version
- output report

This makes replays and diffs possible.

## VeraCrawl Graph Layers

### URL Graph

Nodes:

- URL
- canonical URL
- redirect target
- sitemap URL
- feed item URL

Edges:

- discovered_from
- links_to
- redirects_to
- canonical_of
- paginates_to
- alternate_language_of

### Page Structure Graph

Nodes:

- page snapshot
- DOM section
- heading
- table
- list
- form
- media block
- script data block

Edges:

- contains
- precedes
- labels
- describes
- repeats_template

### Entity Graph

Nodes:

- person
- organization
- product
- article
- event
- location
- document
- claim
- fact

Edges:

- mentions
- authored_by
- published_by
- offers
- priced_at
- located_at
- same_as
- supports
- contradicts

### Task Graph

Nodes:

- crawl job
- run
- frontier item
- extraction candidate
- evidence packet
- verification decision
- memory event

Edges:

- generated
- consumed
- verified
- rejected
- retried
- superseded

## How Graph Analysis Improves Crawling

### Frontier Scheduling

Graph signals can prioritize URLs:

- pages close to verified entities
- hubs that lead to many unvisited details
- pages in clusters with high freshness debt
- pages connected to unresolved evidence conflicts
- bridge pages connecting multiple topics or sections

### Quality Control

Graph analysis can detect:

- canonical loops
- redirect chains
- duplicate clusters
- isolated pages
- suspiciously disconnected facts
- facts without source pages
- high-value entities only seen once
- extraction candidates unsupported by page text

### Reporting

Graph reports should explain:

- what was crawled
- how pages were connected
- which clusters were covered
- which facts were verified
- which areas remain uncertain
- which pages changed materially

## Production Recommendation

Use Graphify's thinking as the structural intelligence layer for AI-guided crawling:

```text
AI agents explore and observe the web.
Graph layer models what was observed and guides the next crawl action.
Evidence layer verifies claims before publication.
Memory layer helps agents plan, adapt, and repair future runs.
```
