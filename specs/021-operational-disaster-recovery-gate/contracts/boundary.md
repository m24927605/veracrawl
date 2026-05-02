# Boundary: Operational Disaster Recovery Gate

- Core DR validation owns contracts and aggregation only.
- Concrete Postgres, Redis/Valkey, and S3-compatible modules are dynamically loaded by CLI/integration code.
- Deterministic fixture data may seed live local runtimes, but cannot be labeled operational pass unless the live integrated infrastructure report contributes refs.
- A single adapter conformance report cannot satisfy operational DR pass.
- No DR report may serialize DSNs, URLs, object-store credentials, artifact bytes, raw secrets, model prompts, browser content, or framework-native state.
