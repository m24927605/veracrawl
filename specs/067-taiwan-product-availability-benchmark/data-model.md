# Data Model: Taiwan Product Availability Benchmark

No new canonical contract type is required. This spec reuses the product
availability contracts introduced in spec 066.

## Reused Entities

### ProductAvailabilityBenchmarkManifest

Adds one fixture instance:

- `id`: `taiwan-top-ecommerce-product-availability`
- `product_name`: SanDisk Extreme microSDXC UHS-I 256GB memory card
- `target_specs`: Shopee Taiwan, momo, PChome 24h
- `expected_completion_result`: `needs_review`
- `expected_operator_status`: `product_availability_partial_sources_blocked`

### ProductAvailabilityTargetSpec

Each target declares:

- platform name
- target URL
- robots URL
- allowed origin
- expected HTTP status/content type
- required identity terms
- expected site result (`pass` for momo/PChome, `needs_review` for Shopee)

### ProductAvailabilityFieldEvidence

Unchanged. Passing field evidence still requires:

- source anchor ref
- artifact ref
- content hash ref
- model/agent/tool/context trace refs
- evidence/verification refs
- command/event/outbox refs
- replay refs

## Extraction Signals

The runtime may accept the following source-backed signals:

- JSON-LD `Product.offers.price`, `priceCurrency`, `availability`
- meta `product:price:amount`
- meta `product:price:currency`
- meta `product:availability`
- generic Chinese availability labels when no stronger structured signal exists

LLM output remains advisory only and cannot become source evidence.
