# Persistence Runtime Boundary Contract

- Core packages may depend on `veracrawl.contracts.*`, `veracrawl.ports.*`, and standard-library reference store helpers.
- Core packages must not import concrete database, queue, cloud, metrics, tracing, HTTP, browser, model SDK, or agent framework clients.
- Concrete infrastructure integrations must implement `ports/persistence.py` and remain outside core runtime logic.
- The reference filesystem store is for deterministic fixture and adapter-contract validation. It must not be documented as the sole production storage strategy.
- Queue correctness remains owned by scheduler contracts; persistence adapters only make transitions durable and replayable.
