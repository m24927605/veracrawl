# Contract: Source Coverage Boundary

- Core packages must not import browser libraries, concrete HTTP clients, document parser SDKs, credential vault SDKs, API clients, storage/queue/model/provider/agent framework SDKs, or `veracrawl.adapters.source_coverage`.
- Source coverage CLI must dynamically import adapter-owned descriptors.
- Adapter-native state is diagnostic only and cannot satisfy canonical replay or completion.
- Raw secrets and unsafe browser side effects cannot be persisted as canonical state.
- Missing live runtime/credential/parser/browser/API refs return `needs_review`.
- This feature does not claim production browser fleet, production credential vault, production parser farm, external API crawling, or production source runtime readiness.
