# Research: Amazon Official Product API Adapter

## Official Source Findings

- Amazon PA-API v5 `GetItems` historically returns item attributes and supports
  resources such as `ItemInfo.Title`, `Offers.Listings.Price`,
  `Offers.Listings.Availability`, and `OffersV2` resources.
- The same public page states PA-API is deprecated on 2026-04-30 and directs
  users to Creators API.
- Amazon Creators API states it provides programmatic access to Amazon product
  data, requires credentials, and has eligibility constraints for approved
  creator/affiliate accounts.

## Decision

The executable adapter targets credentialed Creators API endpoint configuration
instead of hard-coding deprecated PA-API as the production path. The parser
accepts PA-API-shaped JSON so an authorized migration response can still be
validated, but production live pass remains credential-dependent.

## Risks

- Detailed Creators API endpoint docs are account-gated; without operator
  credentials and endpoint configuration, VeraCrawl can only report
  `needs_review`.
- Amazon may change response shapes; the adapter must fail typed missing-field
  diagnostics rather than fabricate price/availability.

