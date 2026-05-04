# Feature Specification: Delivery ETA Offer Sorting Projection

**Feature Branch**: `078-delivery-eta-offer-sorting-projection`  
**Created**: 2026-05-04  
**Status**: Implemented  
**Roadmap Row**: 078  
**Input**: Product crawl results must support downstream website sorting by
price, arrival time, and inventory without fabricating fields that are not
source-backed.

## Summary

Extend the product availability benchmark so VeraCrawl can extract optional
source-backed delivery ETA and shipping fee evidence, compute total price when
currency-compatible evidence exists, and materialize a sortable offer projection
for ecommerce comparison experiences.

This spec does not turn VeraCrawl into a site-specific ecommerce scraper. It
adds general field extraction and projection behavior that applies only when the
accepted source artifact contains field evidence.

## User Scenarios & Testing

### Primary User Story

As a VeraCrawl operator building an ecommerce comparison website, I need product
offer outputs that can be sorted by item price, total price, source-backed
arrival window, and inventory status while preserving source anchors and replay
refs for every accepted field.

### Acceptance Scenarios

1. **Given** a product page contains source-backed price, availability, delivery
   ETA, and shipping fee, **When** the product availability benchmark runs,
   **Then** VeraCrawl records field evidence for each detected field and
   produces sortable offer records.
2. **Given** a product page contains price and availability but no source-backed
   delivery ETA, **When** the benchmark runs, **Then** the offer remains sortable
   by price and availability, and delivery sorting places it after offers with
   known source-backed ETA.
3. **Given** a source is blocked or lacks required product evidence, **When** the
   projection runs, **Then** VeraCrawl records a typed non-pass offer and never
   fabricates price, inventory, or arrival data.

## Functional Requirements

- **FR-001**: System MUST allow `ProductAvailabilityFieldEvidence` rows for
  `delivery_eta` and `shipping_fee` only when they bind to source anchors,
  artifacts, content hashes, verification decisions, command/event/outbox refs,
  and replay refs.
- **FR-002**: System MUST keep `delivery_eta` optional; missing ETA MUST NOT
  fail a price/availability result and MUST NOT be filled from LLM output.
- **FR-003**: System MUST normalize delivery ETA into `min_days` and `max_days`
  only from accepted source text or metadata.
- **FR-004**: System MUST normalize shipping fee into amount and currency; a
  shipping fee evidence row without amount or currency MUST fail contract
  validation.
- **FR-005**: System MUST compute `total_price_amount` only when item price and
  shipping fee use the same currency; otherwise the total price sort value MUST
  remain absent.
- **FR-006**: System MUST materialize `SortableProductOfferRecord` and
  `ProductOfferProjectionReport` contracts with sorted refs for price, total
  price, delivery ETA, and availability.
- **FR-007**: System MUST preserve framework-neutral AI/model trace refs already
  required by product availability extraction; LLM output remains prohibited as
  field source evidence.
- **FR-008**: System MUST update CLI output so downstream website code can read
  offer records and the offer projection report as JSON artifacts.

## Edge Cases

- Free shipping text is accepted only when a price currency is available or the
  source itself declares currency.
- Delivery phrases with same-day, next-day, fixed-day, or day-range language are
  normalized; ambiguous marketing copy is ignored.
- Blocked sources are represented as non-pass offer records with diagnostics.
- Currency mismatch between item price and shipping fee prevents total price
  sorting but does not invalidate the item price evidence.

## Key Entities

- **ProductAvailabilityFieldEvidence**: Source-backed product field evidence row.
- **ProductAvailabilitySiteResult**: Per-site accepted or non-pass product
  evidence result.
- **SortableProductOfferRecord**: Per-site sortable offer projection with source
  refs and sort values.
- **ProductOfferProjectionReport**: Aggregate projection containing sorted offer
  refs and blocked source refs.
- **ProductOfferProjectionManifest**: Fixture contract declaring required sort
  keys and replay requirements.

## Success Criteria

- Focused tests prove delivery ETA and shipping fee extraction without changing
  existing price/availability behavior.
- Offer projection sorting is deterministic for price, total price, delivery
  ETA, and availability.
- Registry validation includes offer projection contracts and events.
- Full validation results are recorded in `tasks.md`; no live delivery data is
  claimed unless source-backed artifacts contain it.

## Assumptions

- Delivery ETA is a field-level ecommerce attribute, not a crawler capability
  claim by itself.
- The first implementation supports common public HTML, metadata, JSON-LD, and
  rendered DOM text patterns; site-specific checkout/cart-only promises remain
  out of scope unless a later authorized session/API spec covers them.
