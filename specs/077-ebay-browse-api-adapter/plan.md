# Implementation Plan: eBay Browse API Adapter

## Context

This spec extends the source-limited eBay finding from 066 by adding an
authorized official API path. It does not add eBay-specific scraper selectors or
access-control bypass behavior.

## Design

- Reuse official ecommerce API contracts and benchmark runtime from 076.
- Add `EbayBrowseApiAdapter` under `veracrawl.adapters.official_apis`.
- Support access-token mode and OAuth client-credentials mode.
- Parse `itemSummaries[0].title`, `price.value`, `price.currency`, and
  `estimatedAvailabilities`.
- Include eBay in `tests/fixtures/us-ecommerce-official-api-product-availability`.

## Boundaries

- eBay SDKs are not imported.
- Access token and client secret values are never written to canonical outputs.
- Missing credentials remain visible needs-review.

## Validation

- Focused ruff.
- Focused mypy.
- Runtime and adapter unit tests.
- CLI integration test for no-credential behavior.
- Live CLI no-credential run that records `needs_review`.

