# Data Model: Amazon Official Product API Adapter

- `EcommerceOfficialApiTargetSpec`: manifest target, platform, API family,
  allowed origin, endpoint, product identifier, required identity terms,
  credential env vars, budgets, and expected result.
- `EcommerceOfficialApiSourceFetch`: source-backed official API fetch with
  content hash, redacted artifact, credential audit, policy, command/event,
  outbox, and replay refs.
- `EcommerceOfficialApiRedactedArtifact`: redacted JSON preview and content
  hash.
- `EcommerceOfficialApiFieldEvidence`: identity, price, or availability field
  bound to source evidence; LLM evidence refs are forbidden.
- `EcommerceOfficialApiSiteResult`: per-site pass/needs-review result.
- `EcommerceOfficialApiBenchmarkReport`: aggregate report for official API
  readiness.

