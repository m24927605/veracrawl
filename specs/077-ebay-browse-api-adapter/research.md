# Research: eBay Browse API Adapter

## Official Source Findings

- eBay Browse API contains `item_summary`, `search_by_image`, and `item`
  resources.
- The `item_summary/search` method searches by keyword, category, ePID, GTIN,
  charity ID, or combinations.
- Search result summaries include `title`, `itemId`, `price`, marketplace, and
  availability-related fields such as estimated availability.

## Decision

Use Browse API `item_summary/search` as the first official source path for eBay
product lookup. It matches VeraCrawl's benchmark question: find a specified
product and obtain source-backed price and availability.

## Risks

- Browse API requires eBay application credentials or an access token.
- Search results may return non-identical listings; required identity terms
  remain mandatory before field evidence can pass.

