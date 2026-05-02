# Requirements Checklist: Browser and Network Acquisition Runtime

- [x] Specification preserves VeraCrawl as a general-purpose AI agent crawler.
- [x] Specification does not introduce single-site scraper assumptions.
- [x] Core dependencies are restricted to contracts, ports, policy, scheduler, durable, artifact refs, and replay.
- [x] Real local HTTP acquisition is required and tested through deterministic benchmark server fixtures.
- [x] Browser execution is represented through contracts, ports, sandbox gates, and deterministic fixtures without core framework coupling.
- [x] Security gates cover egress, private network, robots, rate, size, redirect, timeout, and unsafe browser side effects.
- [x] Replay, artifact, command, event, policy, and scheduler refs are required for pass-capable reports.
- [x] Negative fixture coverage is defined before implementation.
