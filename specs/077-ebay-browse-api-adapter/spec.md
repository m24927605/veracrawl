# Feature Specification: eBay Browse API Adapter

**Feature Branch**: `077-ebay-browse-api-adapter`  
**Created**: 2026-05-04  
**Status**: Implemented  
**Roadmap Row**: 077  
**Input**: eBay public item pages can return access denial in the 066 product
benchmark, so VeraCrawl needs an official Browse API source path for authorized
product search, price, and availability evidence.

## Summary

Add an eBay Browse API adapter behind VeraCrawl's neutral official ecommerce API
port. The adapter MUST use eBay OAuth/app credentials or an operator-provided
access token, query the official `item_summary/search` endpoint, and emit only
source-backed field evidence.

## Functional Requirements

- **FR-001**: eBay official API access MUST run through
  `EcommerceOfficialApiAdapterPort`; core MUST NOT import eBay SDKs or preserve
  eBay-native state.
- **FR-002**: Adapter MUST accept either `EBAY_ACCESS_TOKEN` or
  `EBAY_CLIENT_ID` + `EBAY_CLIENT_SECRET` for OAuth client-credentials flow.
- **FR-003**: Adapter MUST call the official Browse API
  `/buy/browse/v1/item_summary/search` endpoint for query, GTIN, or EPID
  product identifiers.
- **FR-004**: Passing output MUST require source-backed identity, price, and
  availability fields with source anchors, content hash, redacted artifact,
  authorized-source refs, credential audit refs, policy refs,
  command/event/outbox refs, and replay refs.
- **FR-005**: Missing credentials, OAuth errors, HTTP errors, invalid JSON, and
  missing fields MUST be typed `needs_review`.
- **FR-006**: LLM/agent output MUST NOT be accepted as official API source
  evidence.

## Acceptance

- With fake Browse API JSON, eBay field evidence passes and is bound to official
  API source refs.
- Without eBay credentials, the live CLI reports
  `official_api_credentials_unavailable` and publishes no price/inventory.
- OAuth and token paths are isolated inside the concrete adapter.

