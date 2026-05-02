# Contract: Network Acquisition

## Scope

This contract defines real HTTP acquisition through ports and adapters, with deterministic local benchmark fixtures as the only required network target for this slice.

## Required Contracts

- `NetworkRequest`
- `NetworkResponse`
- `RedirectHop`
- `NetworkAcquisitionReport`
- `NetworkClientPort`

## Required Commands And Events

- `execute_http_fetch`
- `record_network_request`
- `record_network_response`
- `record_network_acquisition`
- `network_request_recorded`
- `network_response_recorded`
- `network_acquisition_reported`

## Rules

- Core acquisition must not import concrete HTTP client packages.
- The concrete HTTP adapter must live under `veracrawl.adapters`.
- All HTTP acquisition must carry policy refs before execution.
- Raw HTML artifacts must be represented by refs and content digests.
- Redirect hops must preserve original and final URL lineage.
- Non-success outcomes must not claim raw artifact acceptance.
