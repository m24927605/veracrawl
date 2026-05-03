# Research: Multi-Page Deep Crawl Frontier Benchmark

## Decision: Manifest-Backed Site Graphs For Deterministic Deep Crawl

Use manifest-declared bounded site graphs for fixture execution. Each page
declares URL, canonical URL, depth, page type, source anchors, content hash refs,
links, robots allowance, and optional AI/graph/memory priority influence. This
lets the benchmark prove frontier mechanics without hitting uncontrolled public
sites in routine tests.

Rationale: production deep crawling depends on policy, budgets, canonicalization,
duplicate suppression, replay, and frontier state transitions. Those behaviors
need deterministic negative fixtures before live traversal can be trusted.

Rejected: HTML string scraping inside fixtures. That would overfit DOM shapes and
weaken the general-purpose crawler boundary.

## Decision: AI Influence Is A Traceable Frontier Input, Not Evidence

AI/agent/graph/memory influence is represented on frontier decisions through
model call refs, agent action refs, tool call refs, context bundle refs, graph
frontier refs, and memory refs. These refs can influence priority order and
diagnostics but cannot satisfy source evidence, content hashes, or page coverage.

Rationale: this keeps the framework-neutral agent abstraction intact while
preserving the rule that LLM output is never source evidence.

Rejected: provider-native transcripts in core state. They would couple core to
one model/framework and violate replay requirements.

## Decision: Typed Negative Outcomes Instead Of Silent Coverage Gaps

Duplicate loops, off-origin pollution, robots denial, infinite pagination,
budget exhaustion, and replay mismatch map to explicit
`DeepCrawlFailureType` values and diagnostics. Passing reports must expose
skipped links and stop reasons rather than hide them.

Rationale: production operators need to distinguish safe skip behavior from
false-ready crawl completion.

## Decision: Contract-First CLI Outputs

`veracrawl-deep-crawl-benchmark run` writes the canonical report, page
observations, frontier decisions, stop reasons, and a small summary JSON. CLI
validation checks the manifest's expected result and failure type.

Rationale: later specs 061-064 need reusable quality report artifacts without
depending on terminal text.
