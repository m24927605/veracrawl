# Feature Specification: Amazon Official Product API Adapter

**Feature Branch**: `076-amazon-official-product-api-adapter`  
**Created**: 2026-05-04  
**Status**: Implemented  
**Roadmap Row**: 076  
**Input**: Amazon public product pages can pass in the recorded 066 browser/HTTP
case, but production ecommerce coverage also needs an official authorized API
path when browser/public source evidence is source-limited.

## Summary

Add an Amazon official product API adapter behind VeraCrawl's neutral
authorized-source/ecommerce API port. The adapter MUST keep Amazon-specific
credential handling, request construction, and response parsing outside core,
and MUST report missing or unavailable Amazon credentials as `needs_review`
instead of fabricating product price or inventory.

Amazon's public PA-API v5 page now states PA-API deprecation on 2026-04-30 and
directs integrations to Creators API. Therefore this spec targets a
credentialed Creators API integration point supplied by the operator through
environment configuration. PA-API shaped responses may be parsed for migration
compatibility, but this spec does not claim a new PA-API production path.

## Functional Requirements

- **FR-001**: System MUST define source-backed official ecommerce API contracts
  for target specs, source fetches, redacted artifacts, field evidence, site
  results, and aggregate reports.
- **FR-002**: Amazon official API access MUST run through
  `EcommerceOfficialApiAdapterPort`; VeraCrawl core MUST NOT import Amazon SDKs
  or preserve Amazon-native state.
- **FR-003**: The Amazon adapter MUST require operator-provided
  `AMAZON_CREATORS_API_ENDPOINT` plus `AMAZON_CREATORS_API_BEARER_TOKEN` or
  `AMAZON_CREATORS_API_KEY`.
- **FR-004**: The adapter MUST reject an endpoint outside the manifest's
  `allowed_origin`.
- **FR-005**: Passing output MUST bind identity, price, and availability fields
  to source anchors, redacted artifacts, content hashes, credential grant/audit
  refs, policy refs, command/event/outbox refs, and replay refs.
- **FR-006**: LLM/agent output MUST NOT be accepted as official API source
  evidence.
- **FR-007**: Missing credentials, HTTP errors, invalid JSON, oversized bodies,
  and missing product fields MUST produce typed `needs_review` diagnostics.

## Acceptance

- With fixture/fake Amazon API response, identity, price, and availability field
  evidence pass with authorized-source refs.
- Without Amazon credentials, the live CLI reports
  `official_api_credentials_unavailable` and does not publish fields.
- The CLI writes validation artifacts under the requested output directory.

