# Contract: Website Pattern Coverage Gate

## Target Website Patterns

- `static`
- `sitemap_rss_feed`
- `listing_detail`
- `search`
- `non_destructive_forms`
- `javascript_pages`
- `authenticated_sources`
- `api_like_endpoints`
- `documents`
- `multi_language_pages`
- `drifted_sites`
- `high_volume_sites`

## Required Pass Refs

Each `WebsitePatternCoverageRecord` must include:

- benchmark fixture refs
- source adapter refs
- source evidence refs
- site model and page type refs
- expected output oracle refs
- evidence coverage refs
- policy refs
- artifact, event, and graph oracle refs
- pattern-specific refs
- command refs
- event cursor refs
- outbox refs
- replay bundle refs

## Failure Types

- `website_pattern_missing_runtime_refs`
- `website_pattern_missing_pattern`
- `website_pattern_unsupported_pattern`
- `website_pattern_single_site_assumption`
- `website_pattern_scaffold_only`
- `website_pattern_missing_source_adapter`
- `website_pattern_missing_site_model`
- `website_pattern_missing_output_evidence`
- `website_pattern_missing_pattern_specific_refs`
- `website_pattern_unsafe_interaction`
- `website_pattern_missing_replay_refs`
