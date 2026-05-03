# Data Model: Multi-Page Deep Crawl Frontier Benchmark

## DeepCrawlPageSpec

Declares a crawlable page in a bounded site graph.

- `id`, `url`, `allowed_origin`, `canonical_url`
- `page_type`: listing, detail, pagination, sitemap, feed, canonical, or other
- `depth`, `required_for_coverage`, `robots_allowed`, `private_network`
- `link_urls`, `source_anchor_refs`, `content_hash_ref`, `artifact_ref`
- `ai_prioritized`, `model_call_refs`, `agent_action_refs`, `tool_call_refs`,
  `context_bundle_refs`, `graph_frontier_refs`, `memory_refs`

Validation: HTTP(S) URLs only, canonical URL must be HTTP(S), link refs must be
declared by URL or safely skipped by policy.

## DeepCrawlSiteSpec

Defines one bounded site objective.

- `id`, `allowed_origin`, `seed_urls`, `page_specs`
- `max_depth`, `max_pages`, `rate_budget_ref`, `robots_policy_ref`,
  `private_network_policy_ref`
- `expected_required_page_count`, `expected_page_type_refs`

Validation: at least one seed, positive depth/page limits, all page specs remain
inside the declared owner-service contract boundary.

## FrontierDecisionTrace

Records one keep, skip, prioritize, or stop decision.

- `id`, `site_ref`, `source_page_ref`, `target_url`, `canonical_url`,
  `depth`, `action`, `reason`
- policy, graph, memory, AI/model/agent/tool/context, source anchor, command,
  event cursor, outbox, and replay refs
- `failure_type` and diagnostics for unsafe or mismatched decisions

Validation: passing keep/prioritize/skip/stop decisions require policy, source or
graph provenance, command/event/outbox, and replay refs. AI-prioritized decisions
require all VeraCrawl AI trace ref families.

## DeepCrawlPageObservation

Records a fetched/observed page from the bounded crawl.

- `id`, `site_ref`, `page_spec_ref`, `url`, `canonical_url`, `page_type`, `depth`
- artifact/content hash/source anchor/link provenance/canonical/duplicate/graph
  refs
- policy, command, event cursor, outbox, and replay refs

Validation: passing observations require artifact/hash/source anchor/link
provenance/canonical/graph/policy/command/event/outbox/replay refs.

## DeepCrawlStopReasonRecord

Records why a site crawl stopped.

- `id`, `site_ref`, `reason`, `frontier_remaining_count`, `page_count`,
  `max_depth`, `max_pages`
- policy, command, event cursor, outbox, and replay refs

Validation: passing reports need at least one stop reason per site.

## DeepCrawlQualityReport

Aggregates crawl quality across the fixture.

- counts: site count, required page count, covered page count, observed page
  count, skipped link count, duplicate-suppressed count, off-origin skip count,
  robots-denied skip count, stop reason count
- refs: observations, frontier decisions, stop reasons, graph/link/canonical/
  duplicate/artifact/hash/source anchor/policy/command/event/outbox/replay
- typed failure and diagnostics

Validation: pass requires minimum site/page coverage, full replay refs, no
frontier pollution, duplicate suppression, stop reasons, and manifest expected
result alignment.
