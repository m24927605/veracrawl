# Contract: Adapter Runtime

Adapters implement `SourceAdapterPort`.

Required deterministic adapters:

- HTTP -> `fetch_result`
- sitemap -> `discovered_links`
- RSS -> `discovered_links`
- API-like -> `api_payload`
- document-source -> `document_artifact`

Adapters must not mutate durable state directly. The fetch runtime owns command handling, policy checks, artifact refs, event refs, outbox refs, and replay reports.

Adapter mismatch occurs when an adapter emits a result type outside the mapping in `ADAPTER_RESULT_MAPPING`.
