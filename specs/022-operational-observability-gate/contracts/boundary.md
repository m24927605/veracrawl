# Boundary: Operational Observability Gate

- Core observability validation owns contracts and aggregation only.
- Concrete telemetry backends, collectors, exporters, dashboards, paging systems, and on-call automation are adapter-owned future gates.
- Ops console data, quality reports, dashboard snapshots, failure records, recovery actions, and DR restore reports are observability inputs, not sufficient pass evidence.
- A vendor-native trace, metric, alert, or dashboard cannot satisfy operational observability pass unless it is represented through canonical VeraCrawl contracts with replay, policy, redaction, command, event, outbox, and backend handoff refs.
- No observability report may serialize DSNs, URLs with credentials, object-store credentials, queue credentials, cloud credentials, raw secrets, raw prompts, raw artifacts, browser content, or framework-native state.
