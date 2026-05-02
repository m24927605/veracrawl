# Research: VeraCrawl Export Connectors

## Decision: Build Destination-Neutral Export Contracts First

- **Rationale**: Target docs require file, API, database, warehouse, object store, and queue targets. A single adapter would weaken the product into a destination-specific exporter.
- **Rejected alternative**: Implement a local file export only. Rejected because it would not prove target connector semantics or withdrawal propagation.

## Decision: Make Receipts And Mappings Mandatory

- **Rationale**: Exports are only auditable when destination object IDs and receipts can be reconciled to output refs.
- **Rejected alternative**: Treat dispatch as success. Rejected because it allows silent downstream gaps.

## Decision: Treat Unsupported Withdrawal As Needs Review

- **Rationale**: Some destinations cannot delete or withdraw objects. The platform must emit a reviewable `destination_unsupported` result, not claim propagation.
- **Rejected alternative**: Ignore unsupported withdrawal. Rejected because downstream governance would be unverifiable.

## Decision: Keep Concrete Clients Behind Ports

- **Rationale**: The core must not depend on HTTP, database, object store, queue, warehouse, or agent framework clients.
- **Rejected alternative**: Add SDK dependencies now. Rejected because target architecture calls for replaceable adapters.
