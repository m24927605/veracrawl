# Implementation Plan: Amazon Official Product API Adapter

## Context

This spec extends 066 and 071. It is not a single-site scraper: it adds a
credentialed official-source adapter path for Amazon product evidence while
keeping product-page crawling and official API acquisition behind neutral ports.

## Design

- Add `veracrawl.contracts.ecommerce_official_api` models.
- Add `veracrawl.ports.ecommerce_official_api` as the framework/platform-neutral
  adapter boundary.
- Add `AmazonCreatorsApiAdapter` under `veracrawl.adapters.official_apis`.
- Add `run_ecommerce_official_api_benchmark` runtime that receives an adapter
  factory and emits canonical VeraCrawl refs.
- Add `veracrawl-ecommerce-official-api run-live`.
- Add the shared US official API fixture covering Amazon and eBay.

## Boundaries

- Core contracts/runtime depend only on VeraCrawl contracts and ports.
- Amazon credential and request details live only in
  `src/veracrawl/adapters/official_apis/amazon.py`.
- No hidden endpoints, CAPTCHA bypass, WAF evasion, or public-page scraping is
  introduced by this spec.

## Validation

- Focused ruff.
- Focused mypy.
- Runtime and adapter unit tests.
- CLI integration test for no-credential behavior.
- Live CLI no-credential run that records `needs_review`.

