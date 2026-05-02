# Boundary Contract

- VeraCrawl core must not import concrete queue brokers, storage clients, metrics/tracing backends, cloud SDKs, HTTP clients, browser libraries, or agent frameworks.
- Scale runtime may emit commands/events/refs only; durable mutation remains owned by owner services.
- Autoscaling decisions can change throughput only, not correctness.
- Backpressure and budget pauses require policy refs.
- Dead-letter items require failure records and recovery/review refs.
- Stale leases cannot pass without recovery visibility.
