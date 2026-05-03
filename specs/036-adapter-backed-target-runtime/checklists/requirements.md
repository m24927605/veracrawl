# Requirements Checklist: VeraCrawl Adapter-Backed Target Runtime

## Clarity

- [x] Scope is target runtime adapter-backed acquisition proof, not live Internet crawling.
- [x] Core/adapters boundary is explicit.
- [x] Negative cases and typed failures are enumerated.
- [x] Existing 034 and 035 fixture compatibility is required.

## Completeness

- [x] Contracts are named.
- [x] Runtime report extensions are named.
- [x] CLI materialization path is named.
- [x] Import-boundary proof is named.
- [x] Verification gates are named.

## Non-Deceptive Completion

- [x] Direct source bypass is a failure.
- [x] Adapter result and output refs are required for adapter-backed completion.
- [x] Contract-only or scaffold-only adapter refs cannot claim operational pass.
- [x] Live external crawling is not claimed.
