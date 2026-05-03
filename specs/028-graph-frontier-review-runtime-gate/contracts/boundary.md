# Contract: Graph Frontier Review Boundary

- Core cannot import graph store clients, queue clients, storage clients, browser libraries, model SDKs, agent frameworks, or concrete HTTP clients.
- Graph signal use must remain explainable and policy-backed.
- Unauthorized frontier mutation fails.
- Missing source graph refs, explanations, review routes, or replay refs fail.
- Missing live graph/scheduler/review runtime refs returns `needs_review`.
