# Research: Delivery ETA Offer Sorting Projection

## Decision: Delivery ETA Is Optional Source Evidence

Delivery ETA varies by location, inventory node, shipping method, membership,
and checkout state. Treating ETA as required would incorrectly fail pages that
still provide valid source-backed price and inventory. The projection therefore
sorts known ETA first and keeps unknown ETA explicit.

Rejected alternative: infer ETA from store reputation or LLM reasoning. This
would violate VeraCrawl's evidence boundary because model output is not source
evidence.

## Decision: Shipping Fee Requires Amount And Currency

Shipping fee participates in total price sorting, so amount without currency is
not safe. Free-shipping phrases are accepted only when the price currency or
source declares a currency.

Rejected alternative: assume local currency from domain. This would be a
site/geography heuristic rather than source-backed field evidence.

## Decision: Offer Projection Is A Separate Contract

The product availability report answers whether each site produced source-backed
product fields. The offer projection answers how accepted offers can be sorted.
Keeping these contracts separate keeps extraction and presentation concerns
cohesive without coupling the benchmark to a future website UI.
