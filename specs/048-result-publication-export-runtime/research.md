# Research: Result Publication And Export Runtime

## Decision: Add a row 048 aggregate report instead of overloading export fixtures

Existing export fixtures prove destination-neutral export contracts, but they do
not prove that exports are fed by row 047 source-backed evidence. A dedicated
`ResultPublicationExportRuntimeReport` closes that gap by requiring live
evidence, publication, Result API, export, withdrawal, correction, and replay
refs in one pass condition.

## Decision: Keep concrete connectors outside core

The core runtime builds deterministic contract objects and refs. The CLI
composes row 041-047 prerequisites using existing fixture-local adapters at the
edge. This preserves the framework-neutral, adapter-neutral core rule.

## Decision: Result API is a contract snapshot

The Result API surface is represented as `ResultApiSnapshot`: immutable output
refs, output manifest refs, response artifact/hash refs, privacy lifecycle refs,
and replay refs. This avoids introducing an HTTP server in row 048 while still
making the API materialization auditable and replayable.

## Decision: Passing reports require withdrawal and correction refs

Target architecture requires outputs to be withdrawable and correctable, not
only exportable. Row 048 pass therefore includes export receipts, withdrawal
jobs/attempts, correction records, and destination object mappings.
