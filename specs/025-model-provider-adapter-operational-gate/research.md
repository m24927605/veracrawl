# Research: Model Provider Adapter Operational Gate

## Decision: Provider gate is core-owned, provider adapters are adapter-owned

Core code validates canonical VeraCrawl contracts and does not import concrete provider SDKs. Deterministic contract adapters live in `veracrawl.adapters.model_providers`.

Rationale: This preserves low coupling and lets future OpenAI, Anthropic, Gemini, OpenAI-compatible, local runtime, or other providers enter through the same boundary.

## Decision: Passing report requires every target provider family

The success fixture must include OpenAI, Anthropic, Google Gemini, OpenAI-compatible endpoint, local model runtime, and FutureProvider.

Rationale: A single provider pass does not prove VeraCrawl's provider-neutral target architecture.

## Decision: Missing live provider runtime returns needs_review

Contract-only provider descriptors are useful but cannot prove operational provider access. Missing API credentials, SDK, endpoint, or local runtime refs must return `needs_review`.

Rationale: This avoids false completion claims and matches previous adapter gate patterns.

## Decision: Provider-native transcript is diagnostic only

Provider-native message histories, raw responses, token streams, or tool suggestion payloads cannot become canonical. Canonical state is `ModelRequest`, `ModelResponse`, `ModelCallTrace`, trace refs, command results, policy refs, security/privacy refs, and replay refs.

Rationale: Replay and safety must be provider-independent.

## Decision: Unsafe tool suggestions fail unless blocked

If a provider response suggests unsafe tool use and the adapter cannot show policy/command refs proving the suggestion was blocked, the gate fails.

Rationale: Model output must not bypass tool gateway and owner-service mutation boundaries.
