# Contracts

079 materializes Python/Pydantic contracts in:

- `src/veracrawl/contracts/product_discovery.py`

Registered contracts:

- `ProductDiscoverySourceSpec`
- `ProductDiscoveryCandidate`
- `ProductDiscoveryRunReport`
- `ProductDiscoveryBenchmarkManifest`

Command/event registry coverage:

- `record_product_discovery_candidate`
- `record_product_discovery_run_report`
- `record_product_discovery_manifest`
- `product_discovery_candidate_recorded`
- `product_discovery_run_reported`
- `product_discovery_manifest_recorded`
