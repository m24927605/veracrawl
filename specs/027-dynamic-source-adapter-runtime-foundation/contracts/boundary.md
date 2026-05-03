# Contract: Dynamic Source Runtime Boundary

- Core cannot import `veracrawl.adapters.sources.dynamic_runtime`.
- Core cannot import browser libraries, HTTP clients, document parsers, vault SDKs, API SDKs, storage clients, queue clients, model SDKs, provider SDKs, or agent frameworks.
- Runtime pass cannot be inferred from coverage descriptors alone.
- Missing runtime refs must be `needs_review`.
- Raw secrets and adapter-native state cannot become canonical.
