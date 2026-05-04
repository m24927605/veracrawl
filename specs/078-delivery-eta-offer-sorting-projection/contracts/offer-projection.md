# Contract: Product Offer Projection

Passing offer records require:

- source-backed price evidence ref
- source-backed availability evidence ref
- field evidence refs
- source anchor refs
- artifact and content hash refs
- canonical URL refs
- verification refs
- policy refs
- command/event/outbox refs
- replay refs

Delivery ETA and shipping fee are optional fields. When present, each must have
its own field evidence ref. Shipping fee must include amount and currency.

Projection reports must expose sorted offer refs for:

- price
- total price
- delivery ETA
- availability

Blocked sources must remain typed non-pass records and cannot contribute
fabricated sort values.
