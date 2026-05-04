# Research: US Top Ecommerce Product Price Availability Benchmark

## Decision: Product Detail Pages Before Search Traversal

The benchmark starts with declared public product-page URLs for the specified
product. This isolates price/availability extraction quality from search result
ranking, sponsored item filtering, pagination, and anti-bot behavior.

Search traversal is a later benchmark because it requires more requests and
site-specific drift handling. This spec still keeps target data in manifests so
future search discovery can reuse the contracts.

## Decision: SanDisk 256GB Extreme microSDXC UHS-I Memory Card with Adapter Corpus

Live probes on 2026-05-04 showed:

- Amazon product page for SanDisk 256GB Extreme microSDXC UHS-I Memory Card with Adapter returned HTTP 200 with product
  identity terms and a visible localized price marker (`TWD...`).
- Walmart product page returned HTTP 200 with product identity terms,
  structured-data price, and `OutOfStock` availability markers.
- eBay item pages for comparable SanDisk/AirPods listings returned access
  denial or unstable seller-listing behavior to the benchmark HTTP adapter.

The fixture therefore expects source-backed extraction on Amazon and Walmart and
typed needs-review/access-denied handling for eBay when live HTTP blocks.

## Decision: Preserve Observed Currency

The benchmark does not force USD because public ecommerce pages may localize
currency based on geography or delivery assumptions. It records the raw price
text, normalized amount when parseable, and observed currency.

## Decision: Hosted AI Is Advisory

AI participates through `ModelProviderPort` and `AgentRuntimePort` for identity,
price candidate, availability candidate, and verification decisions. The runtime
accepts fields only when source anchors and artifacts support them.

## Risks

- Product prices and availability change frequently. Tests assert evidence and
  non-empty extraction, not fixed dollar values.
- eBay may block item-page HTTP access. The benchmark must report this honestly.
- Ecommerce pages include many related prices. The extractor prioritizes
  structured product data and visible price markers after identity checks.
