# Boundary Contract

- VeraCrawl core must not import concrete export SDKs, HTTP clients, database clients, warehouse clients, object store clients, queue clients, browser libraries, or agent frameworks.
- Destination-specific delivery must live behind `ExportTargetPort` adapters.
- Export dispatch requires immutable output refs and export policy refs.
- Successful delivery requires destination receipt and external object mappings.
- Withdrawal and correction propagation require destination mappings and policy refs.
- Unsupported withdrawal semantics must be represented as reviewable `destination_unsupported`, not silent success.
