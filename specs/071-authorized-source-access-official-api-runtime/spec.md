# Feature Specification: Authorized Source Access And Official API Runtime

**Feature Branch**: `071-authorized-source-access-official-api-runtime`  
**Created**: 2026-05-04  
**Status**: Implemented
**Roadmap Row**: 071  
**Input**: Production-grade closure requirement: sites that require authorized access or official APIs need first-class, policy-compliant adapters.

## Summary

Add a production runtime for authorized source access. VeraCrawl must support
official APIs and explicitly authorized credentialed sessions as source adapters
without leaking secrets, bypassing site controls, or coupling core to provider
SDKs.

## User Scenarios

1. Given an official API credential for an ecommerce platform, VeraCrawl fetches
   product fields through the API adapter and binds them to source artifacts,
   hashes, evidence anchors, verification refs, and replay refs.
2. Given an authorized read-only session for a site, VeraCrawl uses the session
   only within approved origin/scope and records credential audit refs,
   redaction refs, and policy decisions.
3. Given an unavailable credential, unauthorized origin, login wall, challenge,
   or terms denial, VeraCrawl records needs-review or failure without bypass.

## Functional Requirements

- **FR-001**: System MUST define `AuthorizedSourceProfile`,
  `OfficialApiSourceSpec`, `CredentialUseGrant`, `CredentialUseAudit`,
  `AuthorizedSourceResult`, and `RedactedSourceArtifact` contracts.
- **FR-002**: System MUST support official API adapters through source ports,
  not direct provider SDK coupling in core.
- **FR-003**: System MUST support credentialed read-only browser/HTTP sessions
  only with explicit grant, origin scope, purpose, retention, and redaction
  policy.
- **FR-004**: System MUST produce artifacts and evidence refs for API responses
  and credentialed source observations.
- **FR-005**: System MUST redact secrets, session tokens, cookies, account
  identifiers, and private data from persisted artifacts and replay.
- **FR-006**: System MUST fail when credential use exceeds scope, leaks raw
  secrets, mutates state, accesses cart/checkout, or bypasses challenge flows.
- **FR-007**: System MUST record cost/rate limits and provider quota refs.

## Non-Goals

- No credential theft, shared-user session scraping, CAPTCHA solving, paywall
  bypass, WAF evasion, or unauthorized private data extraction.
- No platform-specific logic in core. Provider-specific behavior lives in
  adapters.

## Required Tests

- Contract tests for API specs, credential grants, redaction, audit, and
  authorized results.
- Negative tests for missing grant, out-of-scope origin, secret leakage, raw
  replay leakage, unsafe mutation, challenge bypass attempt, and missing audit.
- Adapter import-boundary tests.
- Live or simulated official API fixture with replayable source-backed evidence.

## Completion Gate

Authorized source access can provide production evidence through official APIs or
approved read-only sessions, while unauthorized access remains blocked and
visible.
