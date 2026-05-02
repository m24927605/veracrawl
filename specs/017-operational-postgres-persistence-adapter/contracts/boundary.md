# Operational Postgres Adapter Boundary

- Core packages may define contracts, ports, and conformance harnesses.
- Core packages must not statically import `veracrawl.adapters`, `psycopg`, or concrete database/queue/cloud clients.
- Postgres client imports are allowed only inside `veracrawl.adapters.persistence.postgres`.
- CLI may dynamic-import adapter modules but must not make core services depend on them.
- A `postgres_contract` descriptor can only report `needs_review`; operational `pass` requires `postgres` adapter kind and live conformance execution.
