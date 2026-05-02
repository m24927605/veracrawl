# Contract: Graph Build

Graph build pass requires:

- at least one input ref
- deterministic node refs
- deterministic edge refs
- edge provenance refs
- graph build manifest
- projection watermark
- command, event, outbox, policy, and replay refs

Graph nodes and edges must be deduplicated by stable keys. Provenance refs must be
retained when duplicate input links collapse to a single edge.
