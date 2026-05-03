# Research: Dynamic Source Adapter Runtime Foundation

## Decision: Core validates runtime records; adapters build concrete records

Rationale: Core must not import browser, parser, vault, API, HTTP, storage, queue, model, provider, or agent framework SDKs. Adapter-owned deterministic/local builders can exercise existing runtime functions where available and emit canonical records for non-fetch adapters.

## Decision: Non-fetch runtime records are first-class

Rationale: Authorized session, manual seed, file import, and prior snapshot do not naturally produce fetch attempts. Passing them through fake fetch/page snapshot refs would violate `docs/10` and previous source coverage rules.

## Decision: Missing live runtime is needs_review

Rationale: Deterministic runtime foundation proves architecture shape, not external runtime availability. Production browser/parser/session/API availability must be represented by live runtime refs.

## Decision: Dynamic CLI imports adapter-owned builder

Rationale: The CLI can load `veracrawl.adapters.sources.dynamic_runtime` dynamically while core remains dependency-neutral.
