# Research: Top Ecommerce Live AI Benchmark

## Decision: Compose Existing Rows 055 And 056

Use `veracrawl-real-benchmark` for live, robots-gated public HTTP acquisition
and `veracrawl-real-ai-benchmark` for AI decision traces. This avoids a new HTTP
or agent path and keeps core coupled only to contracts and ports.

Alternatives rejected:

- Site-specific ecommerce scraper modules: rejected because they violate the
  general-purpose crawler requirement.
- Browser or anti-bot bypass for this benchmark: rejected because this request
  can be tested with public homepage HTTP entry points and must not bypass
  policy.
- LLM-only analysis without live artifacts: rejected because model output is not
  source evidence.

## Decision: Corpus Selection

United States targets are Amazon, Walmart, and eBay because current ecommerce
ranking sources consistently list them among the largest US ecommerce
companies/sites.

Taiwan targets are Shopee Taiwan, momo Shopping, and PChome 24h. Source rankings
vary by methodology: traffic-only ecommerce category lists may put Coupang or
Taobao in the third position, while Taiwan ecommerce platform lists and organic
shopping rankings keep PChome among the top local platforms. The benchmark
therefore documents this as a selected local ecommerce corpus, not a universal
official top-three ranking.

## Decision: Homepage/Public Entry Only

The fixture uses one homepage target per origin. This is the minimum ethical
large-site experiment that can be run repeatedly without login, checkout,
personal data, hidden APIs, or high request volume.

Follow-up work for category/product/deep crawl must be a separate authorized
corpus with explicit robots/policy gates and quality oracles.

## Decision: Hosted LLM Validation

Hosted validation uses the existing OpenAI Responses API adapter behind
`ModelProviderPort`. The CLI loads `OPENAI_API_KEY` from the environment or
`~/.env`, writes framework-neutral `ModelRequest`, `ModelResponse`, and
`ModelCallTrace` refs, and keeps raw model text out of source evidence.

## Risks And Mitigations

- Large ecommerce homepages may return regional, consent, bot-defense, or
  maintenance pages. The benchmark uses coarse fragments and records any
  mismatch as drift rather than bypassing.
- Robots policies may change. The benchmark accepts only declared robots status
  codes and `can_fetch` pass.
- Hosted model latency/cost may vary. The task log records actual run results
  and does not assert stable production quality from one run.
