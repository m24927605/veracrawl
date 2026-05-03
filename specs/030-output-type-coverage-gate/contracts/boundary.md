# Contract Boundary: Output Type Coverage

## Allowed Dependencies

- `veracrawl.contracts`
- deterministic runtime helpers in `veracrawl.publish`
- standard library JSON/argparse/path modules in CLI

## Forbidden Core Dependencies

- storage clients
- queue clients
- export target SDKs
- browser runtimes
- model SDKs
- agent frameworks
- HTTP clients
- site-specific scrapers

## Evidence Boundary

Only source evidence refs and accepted prior output refs may satisfy publication evidence requirements. Candidate refs, graph refs, memory refs, agent reasoning refs, temporal KG refs, and output coverage records are not source evidence.
