# Research: Live Evidence And Verification Runtime

## Decisions

### Reuse field evidence and verification helpers

`build_field_evidence`, `verify_evidence_packet`, and
`review_verification_decision` already express the source-anchor, verification,
and review contracts. The new runtime composes them behind row 046 prerequisites
and adds target failure gates.

### Non-source context is diagnostic only

Graph, memory, and agent reasoning refs may be present for review context, but
they do not satisfy `EvidencePacket.source_evidence_refs`.

### Publication remains blocked

047 produces verification and review refs only. Any publication/export/output
ref is a failure because 048 owns publication/export.

## Alternatives Considered

- **Use graph/memory as fallback evidence**: rejected because source-backed
  evidence is mandatory for publication.
- **Call publication gates here**: rejected because 048 owns result publication
  and export runtime.
