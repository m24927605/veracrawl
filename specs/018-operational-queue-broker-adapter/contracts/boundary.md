# Operational Queue Broker Adapter Boundary

- Core packages may define contracts, ports, and conformance harnesses.
- Core packages must not statically import `veracrawl.adapters`, `redis`, or concrete database/queue/cloud clients.
- Redis client imports are allowed only inside `veracrawl.adapters.queue_brokers.redis`.
- CLI may dynamic-import adapter modules but must not make core services depend on them.
- Persistence queue operation refs cannot claim live broker pass; operational `pass` requires Redis/Valkey adapter kind and live conformance execution.
