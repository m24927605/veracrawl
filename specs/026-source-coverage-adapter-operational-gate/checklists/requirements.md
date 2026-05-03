# Requirements Checklist: Source Coverage Adapter Operational Gate

- [x] No single-site scraper assumptions.
- [x] Python implementation and low-coupling/high-cohesion boundaries preserved.
- [x] Core remains browser/parser/vault/API/source-runtime SDK neutral.
- [x] Source coverage adapter loading is dynamic and adapter-owned.
- [x] Raw secret, native state, unsafe browser side-effect, and source-specific hack boundaries are explicit.
- [x] Missing live runtime/credential/parser/browser/API refs return `needs_review`.
- [x] Negative fixtures cover unsafe and incomplete source mappings.
- [x] Replay, policy, observability, and security/privacy refs are required for pass.
