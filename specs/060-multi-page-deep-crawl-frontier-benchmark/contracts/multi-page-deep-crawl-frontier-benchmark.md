# Contract: Multi-Page Deep Crawl Frontier Benchmark

## CLI

```sh
uv run --python python3.12 --extra dev veracrawl-deep-crawl-benchmark run \
  tests/fixtures/deep-crawl-quality-corpus \
  --profile quality \
  --out .veracrawl-real-runs/deep-crawl-quality-corpus
```

## Inputs

`manifest.yaml` is JSON-compatible and validates as
`DeepCrawlQualityManifest`.

Required oracle files:

- `oracles/expected_outputs.yaml`
- `oracles/expected_events.yaml`
- `oracles/expected_deep_crawl.yaml`
- `oracles/expected_replay.yaml`
- `oracles/thresholds.yaml`

## Outputs

The CLI writes:

- `deep_crawl_report.json`
- `frontier_decisions.json`
- `page_observations.json`
- `stop_reasons.json`
- `summary.json`

`summary.json` includes:

- `ok`
- `fixture_id`
- `completion_result`
- `operator_status`
- `site_count`
- `covered_page_count`
- `observed_page_count`
- `frontier_decision_count`
- `stop_reason_count`
- `duplicate_suppressed_count`
- `replay_bundle_count`

## Pass Contract

A passing quality fixture must:

- cover at least 5 bounded sites and at least 50 required pages
- record every keep/skip/prioritize/stop frontier decision
- enforce depth, page, origin, robots, rate, private-network, and replay gates
- suppress duplicate canonical pages
- record stop reasons for every site
- attach source anchor/artifact/content hash/link provenance/canonical/graph refs
  to page observations
- attach policy/command/event/outbox/replay refs to decisions, observations,
  stop reasons, and report
- attach VeraCrawl model/agent/tool/context refs when AI influences priority

## Failure Contract

Negative fixtures must fail with one of:

- `deep_crawl_duplicate_not_suppressed`
- `deep_crawl_frontier_pollution`
- `deep_crawl_robots_denial_bypassed`
- `deep_crawl_budget_exhausted`
- `deep_crawl_infinite_pagination`
- `deep_crawl_replay_mismatch`
- `deep_crawl_insufficient_page_coverage`

No failing fixture may emit a false `deep_crawl_completed` operator status.
