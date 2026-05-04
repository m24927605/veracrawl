# Contract: Product Price Availability Benchmark

## CLI

```text
veracrawl-product-availability-benchmark run \
  tests/fixtures/us-top-ecommerce-product-availability \
  --profile target \
  --out .veracrawl-real-runs/us-top-ecommerce-product-availability
```

Hosted OpenAI run:

```text
veracrawl-product-availability-benchmark run \
  tests/fixtures/us-top-ecommerce-product-availability \
  --profile target \
  --model-provider openai \
  --openai-model gpt-5.4-mini \
  --out .veracrawl-real-runs/us-top-ecommerce-product-availability-openai
```

Browser DOM source required run:

```text
veracrawl-product-availability-benchmark run \
  tests/fixtures/us-top-ecommerce-product-availability \
  --profile target \
  --model-provider openai \
  --openai-model gpt-5.4-mini \
  --browser-source-required \
  --out .veracrawl-real-runs/us-top-ecommerce-product-availability-openai-browser-source-required
```

Expected aggregate for the live corpus:

```json
{
  "ok": true,
  "completion_result": "needs_review",
  "operator_status": "product_availability_partial_sources_blocked",
  "site_count": 3,
  "passing_site_count": 2,
  "blocked_site_count": 1
}
```

## Evidence Contract

Each passing field must include:

- source anchor ref
- artifact ref
- content hash ref
- canonical URL ref
- model call trace ref
- agent action trace ref
- tool call trace refs
- context bundle trace ref
- evidence packet ref
- verification decision ref
- command/event/outbox refs
- replay bundle ref

The `artifact_ref` can point to the HTTP raw artifact or, when browser fallback
or browser source required mode is used, to a read-only browser DOM artifact.
The field value still must come from source text bound to `content_hash_ref`;
LLM output never satisfies the source evidence fields.

## Blocked Source Contract

When a site blocks access or does not expose price/availability:

- no price or availability field is accepted
- `failure_type` is set
- diagnostics include source status
- aggregate report becomes `needs_review` when at least one other source passes
  and no fabricated values are present

## Boundary Contract

Core code must not import OpenAI SDKs, agent frameworks, browser stealth
tooling, site-specific scraper modules, or hidden ecommerce APIs. Concrete model
access lives behind `ModelProviderPort`; concrete HTTP access lives behind
network adapters; concrete browser rendering lives behind the browser adapter
port.
