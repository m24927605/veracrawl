# Research: Schema Extraction Candidate Runtime

## Decisions

### Reuse existing candidate helpers

`build_extraction_strategy` and `create_anchored_candidate` already create
generic strategies and anchored candidates. The new runtime wraps them with row
045 prerequisites, schema validation refs, model/tool trace refs, rejection
diagnostics, and replay gates.

### Keep model/tool traces framework-neutral

046 records VeraCrawl refs such as `model-trace:<fixture>:schema-extraction`
and `tool-trace:<fixture>:extract-fields`. It does not call a model provider,
agent framework, or framework-native tool runtime. Real model and framework
adapters are reserved for 049.

### Keep candidates unpublished

Candidates remain intermediate extraction records. Any publication/export/output
ref in a passing schema extraction report is a contract violation.

### Drift repair is needs-review

When normalized anchors or schema expectations suggest drift, the runtime emits
drift signal, rejection, and repair recommendation refs with `needs_review`
rather than claiming pass.

## Alternatives Considered

- **Persist provider-native traces**: rejected because core state must remain
  framework-neutral and replayable through VeraCrawl contracts.
- **Treat exploratory schemas as always allowed**: rejected because exploratory
  schemas must be explicit operator-approved context.
- **Publish candidate records directly**: rejected; publication requires 047 and
  048 evidence, verification, and output gates.
