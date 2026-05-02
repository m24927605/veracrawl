# MemPalace Research Notes

Repository studied: `https://github.com/MemPalace/mempalace`

## Core Takeaway

MemPalace is useful for VeraCrawl because it provides a practical model for long-term AI agent memory. A general-purpose AI crawler needs this memory to avoid relearning site structure, extraction strategies, failure modes, and repair tactics on every run:

- preserve original content as drawers
- create compact closet indexes that point back to drawers
- scope retrieval by wing and room metadata
- use L0-L3 memory layers to control context size
- maintain a temporal knowledge graph
- expose memory operations through MCP tools
- keep agent diaries and hooks for automatic checkpointing

For VeraCrawl, MemPalace should be treated as a memory architecture, not as the crawler itself.

## Memory Palace Mapping

```text
MemPalace Concept -> VeraCrawl Concept

Palace  -> Crawl memory system
Wing    -> project, site, customer, domain, or agent
Room    -> page type, topic, section, entity type, or task intent
Hall    -> fact references, events, discoveries, problems, preferences, advice
Drawer  -> raw page text, DOM segment, extraction trace, task event
Closet  -> compact pointer index to drawers
Tunnel  -> cross-site or cross-project structural similarity
Layer   -> startup and retrieval context budget
Diary   -> per-agent decision and observation log
KG      -> temporal facts and relationships
```

## What To Borrow

### 1. Drawer-first Storage

MemPalace stores verbatim content as the durable source. VeraCrawl should do the same.

For crawling, drawers can store:

- raw text chunks
- important DOM segments
- structured data blocks
- table extracts
- HTTP metadata summaries
- parser outputs
- extraction traces
- agent observations

Drawers should never be replaced by summaries. Summaries and embeddings are indexes.

### 2. Closet Pointer Layer

Closets are compact index lines that point to drawers.

Crawler closet examples:

```text
product price|SKU123, ACME Widget|url=...|page_type=product|->drawer_abc
author profile|Jane Doe, Example Corp|url=...|page_type=profile|->drawer_def
pagination|page 2, listing, category shoes|url=...|->drawer_ghi
```

Closets should improve retrieval speed and ranking, but should not gate access to drawers.

### 3. L0-L3 Memory Stack

MemPalace's memory stack is directly applicable to crawler agents.

```text
L0 Identity:
  crawler role, tool boundaries, current project, durable constraints

L1 Essential Story:
  important site history, last run summary, known page types, known failures

L2 Room Recall:
  scoped retrieval for current site, page type, entity, or task

L3 Deep Search:
  cross-site, cross-project, historical search
```

This keeps agent context bounded while still allowing deep recall when needed.

### 4. Temporal Knowledge Graph

MemPalace's temporal KG design is critical for crawling because web facts and crawler behavior both change. VeraCrawl must keep two namespaces separate:

- Publication temporal KG: derived only from verified facts, accepted published outputs, and canonical verification/publication/conflict/supersession/invalidation events.
- Operational temporal memory: derived from crawler observations, memory events, selector behavior, page type behavior, failures, and repairs.

Publication temporal KG records can look like:

```text
Product -> price -> 99.00 [valid_from, valid_to, confidence, source_drawer]
Page -> canonical_url -> URL [valid_from, valid_to, source_snapshot]
```

Operational temporal memory records can look like:

```text
Selector -> extracts -> Product.price [valid_from, valid_to, confidence]
Site -> has_page_type -> ProductPage [valid_from, valid_to]
```

Operational temporal memory can guide planning and repair, but it cannot support publication evidence or authoritative entity identity. Old publication facts and operational records should be invalidated or superseded, not simply overwritten.

### 5. Hybrid Search

MemPalace combines metadata filtering, vector search, BM25, closet boost, and fallback search.

VeraCrawl should use the same retrieval mindset:

- filter by project/site/page type/run first
- combine BM25 for exact identifiers and vector search for semantic recall
- use closet hits as ranking boosts
- hydrate drawers for exact source context
- apply freshness penalties
- preserve fallback paths when vector search is unavailable

### 6. Agent Diaries

Each agent should have its own diary.

Suggested diaries:

- planner diary
- frontier diary
- fetcher diary
- extractor diary
- verifier diary
- memory diary
- ops diary

Diary entries should include:

- task ID
- run ID
- observed context
- decision
- reason
- related evidence
- related memory
- outcome

### 7. Hooks And Checkpointing

MemPalace uses hooks to save important context before sessions end or compress.

VeraCrawl can adapt this for:

- after each crawl batch
- before worker shutdown
- before agent context compression
- after verification failures
- after schema drift detection
- after frontier reprioritization

The objective is to avoid losing operational knowledge.

### 8. Source Adapter Contract

MemPalace's source adapter idea maps well to crawler inputs.

VeraCrawl source adapters:

- `static_html`
- `browser_snapshot`
- `sitemap`
- `rss`
- `api_export`
- `file_import`
- `manual_seed`
- `prior_snapshot`

Each adapter should declare:

- supported source type
- metadata schema
- transformation list
- privacy class
- version token
- idempotency key
- freshness semantics

## Important Caution

Agent memory is not proof. It is a planning prior.

If memory says a selector worked yesterday, the current run must still verify the extracted value against current evidence.

If memory says a page contains a fact, the fact must still be anchored to the current or selected historical snapshot.

## Production Recommendation

Use MemPalace as VeraCrawl's memory kernel for AI-native crawling:

```text
Graph layer maps the web.
Evidence layer proves facts.
Memory layer helps agents remember how to crawl, extract, verify, and repair.
```

This combination is stronger than a crawler, a vector database, or an agent loop alone.
