# Boundary Contract: Product Acceptance Gate

`veracrawl.product_acceptance` and `veracrawl.cli.product_acceptance` may import:

- `veracrawl.contracts`
- `veracrawl.product_acceptance`
- Python standard library modules

They must not import concrete:

- storage adapters or database drivers
- queue or broker clients
- browser automation runtimes
- HTTP clients
- model SDKs
- agent frameworks
- UI frameworks
- export target SDKs
- site-specific scraper modules

Product acceptance proof must come from VeraCrawl-owned contract refs, not:

- mock UI screenshots as the only proof
- manifest-only or scaffold-only fixture refs
- contract-only technical reports
- single-site demos
- framework-native runtime state
- raw browser, storage, queue, HTTP, export, or UI SDK state
