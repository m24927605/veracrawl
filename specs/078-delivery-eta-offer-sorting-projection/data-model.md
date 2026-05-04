# Data Model: Delivery ETA Offer Sorting Projection

## ProductAvailabilityFieldEvidence

Adds supported field names:

- `delivery_eta`: raw source text plus normalized day window.
- `shipping_fee`: raw source text plus amount and currency.

Shipping fee evidence requires amount and currency. Delivery ETA evidence does
not store money fields.

## ProductAvailabilitySiteResult

Adds optional accepted fields:

- `delivery_evidence_ref`
- `delivery_eta_raw_text`
- `delivery_eta_min_days`
- `delivery_eta_max_days`
- `shipping_fee_evidence_ref`
- `shipping_fee_raw_text`
- `shipping_fee_amount`
- `shipping_fee_currency`
- `total_price_amount`
- `total_price_currency`

## SortableProductOfferRecord

One record per product target. Passing records carry source-backed price and
availability refs, optional delivery/shipping refs, sort values, source anchors,
artifacts, content hashes, canonical URL refs, verification refs,
policy/command/event/outbox refs, replay refs, and completion status.

Non-pass records carry blocked source refs, failure type, diagnostics, and do
not fabricate sort values.

## ProductOfferProjectionReport

Aggregates offer records and materializes:

- `sorted_by_price_refs`
- `sorted_by_total_price_refs`
- `sorted_by_delivery_refs`
- `sorted_by_availability_refs`
- evidence refs for price, availability, delivery ETA, and shipping fee
- blocked source refs and diagnostics

## ProductOfferProjectionManifest

Declares the product availability fixture, required sort keys, expected
completion result, operator status, and required ref types.
