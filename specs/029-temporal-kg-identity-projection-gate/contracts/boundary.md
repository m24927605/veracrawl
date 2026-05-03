# Contract Boundary: Temporal KG Identity Projection

## Allowed Dependencies

- `veracrawl.contracts`
- deterministic runtime helpers in `veracrawl.graph`
- standard library JSON/argparse/path modules in CLI

## Forbidden Core Dependencies

- concrete graph store clients
- agent frameworks
- model SDKs
- browser runtimes
- storage clients
- queue clients
- export target clients
- site-specific scraper modules

## Mutation Boundary

Temporal KG state changes are represented by contracts and command/event refs. Concrete mutation is owned by future graph/projection services behind ports; this slice must not directly mutate a graph database.

## Evidence Boundary

Temporal KG identity, projection, adjudication, graph signal, memory, and agent reasoning refs are diagnostics or planning/review inputs only. Publication source evidence remains source artifacts, source anchors, evidence packets, verified facts, and accepted published output refs.
