# Research: Taiwan Top Ecommerce Product Availability Benchmark

## Platform Selection

Decision: Use Shopee Taiwan, momo, and PChome 24h as the Taiwan top ecommerce
platform set.

Rationale: Current public rankings consistently place Shopee Taiwan and momo at
the top, with PChome treated as a major Taiwan ecommerce platform in app/platform
rankings and the existing VeraCrawl row 065 market validation corpus. Some
traffic rankings include non-comparable sites or newer entrants; this benchmark
keeps the same platform set already represented in row 065.

## Product Selection

Decision: Use SanDisk Extreme microSDXC UHS-I 256GB as the comparable product
family.

Rationale: Public pages exist on Shopee Taiwan, momo, and PChome 24h. Product
names vary slightly by seller and distributor, but required identity terms
(`SanDisk`, `Extreme`, `microSDXC`, `256GB`) are stable.

## Source Behavior Probe

- Shopee Taiwan product page returned HTTP 200 but only a JavaScript application
  shell; product API probes returned HTTP 403. Treat as source limitation /
  needs-review unless browser/API support later provides authorized source
  evidence.
- momo mobile product page returned public product meta tags including
  `product:price:amount`, `product:price:currency`, and
  `product:availability`.
- PChome 24h product page returned public JSON-LD Product/Offer with price,
  currency, and availability.

## Implementation Decision

Reuse `veracrawl-product-availability-benchmark` and extend extraction with:

- product meta price amount/currency parsing
- product meta availability parsing
- generic Chinese availability label support

Rejected alternatives:

- Shopee stealth/browser challenge bypass: violates policy.
- Site-specific Shopee/momo/PChome scraper modules: violates general-purpose and
  low-coupling constraints.
- Search-engine snippets as evidence: not source evidence from the platform.
