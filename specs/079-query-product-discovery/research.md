# Research: Query Product Discovery And Offer Ranking

## Decision: Search/List Entry Points, Not Product URLs

The manifest declares source search/listing entry URLs, not product target URLs.
This preserves the distinction between "where to start searching" and "which
product page to extract."

Rejected alternative: Accepting a list of product URLs and labeling it
discovery. That is the exact failure this spec fixes.

## Decision: Generic Candidate URL Extraction

The first runtime extracts candidate URLs from:

- HTML anchors with source-backed href and anchor text
- Script/text URL patterns for product-like paths
- Relative URLs normalized against the search page

Candidate URL patterns are manifest configuration, not code branches for one
site. This allows PChome `/prod/...`, Yahoo `gdsale/...`, momo `goods.momo`,
or future patterns without adding scraper modules.

## Decision: Candidate URLs Remain Advisory Until Product Evidence Passes

Search results can include ads, accessories, variant products, plans, bundles,
or stale pages. A discovered URL only becomes a sortable offer after the
existing product availability runtime verifies product identity, price,
availability, source evidence, and replay refs.

## Decision: Identity Rejection Uses Product Identity Text When Available

Full product pages often include navigation to other variants. Rejected terms
such as `Pro` or `17e` must be evaluated against product identity text
(`json-ld name`, product meta title, `og:title`, `<title>`, heading text) when
available. This reduces both false negatives and false positives.

## Decision: HTTP First For 079

The first query discovery runtime is HTTP/search-page based. Browser discovery
can be added later through the browser port, but 079 must already report
JavaScript-only or source-limited search pages honestly.

## Open Risks

- Some ecommerce search pages expose product links only after JavaScript
  rendering or API calls. These sources will be needs-review in 079.
- Search result order and product page content drift frequently. Live validation
  must record actual observed outcomes rather than hard-coded expectations.
