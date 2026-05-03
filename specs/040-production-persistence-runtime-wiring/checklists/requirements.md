# Requirements Checklist: Production Persistence Runtime Wiring

- [x] Requirements preserve general-purpose AI crawler architecture.
- [x] Requirements do not introduce a single-site scraper or concrete cloud/provider dependency in core.
- [x] Requirements explicitly cover canonical state persistence after adapter reopen.
- [x] Requirements explicitly cover event cursor, outbox, idempotency, artifact index, queue lease, policy, and replay refs.
- [x] Requirements include duplicate-safe replay.
- [x] Requirements include queue recovery.
- [x] Requirements include negative fixtures for missing refs and false pass prevention.
- [x] Requirements reference docs/07, docs/08, docs/09, docs/10, docs/11, and constitution constraints.
