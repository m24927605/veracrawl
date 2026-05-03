# Research: Source Coverage Adapter Operational Gate

## Decision: Source coverage gate is core-owned, source coverage descriptors are adapter-owned

Core code validates canonical VeraCrawl contracts and does not import concrete browser, parser, vault, API, HTTP, storage, queue, model, provider, or agent framework SDKs.

## Decision: Passing report requires every target source adapter family

The success fixture must include HTTP, sitemap, RSS, browser snapshot, authorized session, API-like source, document source, file import, manual seed, and prior snapshot.

Rationale: Partial adapter coverage cannot be labeled target source coverage.

## Decision: Adapter-specific natural refs are required

Browser snapshot requires browser interaction and page snapshot refs. Authorized session requires credential audit refs. API-like source requires API payload refs. Document/file adapters require document artifact refs. Manual seed and prior snapshot require adapter-native natural result refs without fake fetch refs.

## Decision: Missing live runtime returns needs_review

Contract-only descriptors cannot prove operational browser/parser/session/API/source runtime availability.

## Decision: Unsafe browser side effects and raw secrets fail

Browser side effects and raw credential exposure are safety violations, not review-only gaps.
