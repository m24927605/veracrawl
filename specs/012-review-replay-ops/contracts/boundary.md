# Boundary Contract

- VeraCrawl core must not import concrete agent frameworks, model SDKs, browser automation libraries, storage clients, queue clients, graph stores, memory stores, export targets, or HTTP clients for this slice.
- Ops console runtime must produce typed records and refs only; it must not mutate hidden global state.
- Recovery actions that can create side effects must be represented as policy/review/approval-gated records.
- Failure cases must produce `FailureRecord` and `OpsConsoleReport` failure details instead of passing with missing refs.
- Review, replay, and quality dashboard records may inform operators and agents, but they do not replace source evidence for publication.
