# Quickstart: Multi-Page Deep Crawl Frontier Benchmark

Run the deterministic deep crawl quality fixture:

```sh
uv run --python python3.12 --extra dev veracrawl-deep-crawl-benchmark run \
  tests/fixtures/deep-crawl-quality-corpus \
  --profile quality \
  --out .veracrawl-test-runs/deep-crawl-quality-corpus
```

Inspect outputs:

```sh
jq . .veracrawl-test-runs/deep-crawl-quality-corpus/summary.json
jq . .veracrawl-test-runs/deep-crawl-quality-corpus/deep_crawl_report.json
jq . .veracrawl-test-runs/deep-crawl-quality-corpus/frontier_decisions.json
```

Expected pass characteristics:

- at least 5 sites
- at least 50 required pages covered
- frontier decisions for keep, skip, prioritize, and stop
- duplicate canonical URLs suppressed
- off-origin/private/robots-denied links skipped by policy
- AI-prioritized links include VeraCrawl model/agent/tool/context refs
- command/event/outbox/replay refs present on every recorded state transition
