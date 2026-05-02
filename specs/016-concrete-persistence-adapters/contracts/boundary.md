# Concrete Persistence Adapter Boundary

- Core packages may define contracts, ports, and conformance harnesses.
- Core packages must not statically import `veracrawl.adapters` or concrete database/queue/cloud clients.
- SQLite implementation may import `sqlite3` only inside `veracrawl.adapters.persistence`.
- Postgres support in this slice is a contract descriptor and conformance harness only; it must not claim operational production readiness.
- Adapter CLI may dynamic-import adapter modules but must not make core services depend on them.
