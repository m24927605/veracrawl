# Data Model: eBay Browse API Adapter

This spec uses the shared official ecommerce API models:

- `EcommerceOfficialApiTargetSpec(platform="ebay")`
- `EcommerceOfficialApiSourceFetch`
- `EcommerceOfficialApiRedactedArtifact`
- `EcommerceOfficialApiFieldEvidence`
- `EcommerceOfficialApiSiteResult`
- `EcommerceOfficialApiBenchmarkReport`

The eBay parser maps:

- `itemSummaries[0].title` to identity;
- `itemSummaries[0].price.value` and `.currency` to price;
- `itemSummaries[0].estimatedAvailabilities[0].estimatedAvailabilityStatus` to
  availability.

