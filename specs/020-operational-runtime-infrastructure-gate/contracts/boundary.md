# Boundary Contract: Operational Runtime Infrastructure Gate

- Core gate code must not import `veracrawl.adapters`, `psycopg`, `redis`, `boto3`, `botocore`, cloud SDKs, browser libraries, model SDKs, or agent frameworks.
- `veracrawl-infrastructure` may dynamically import concrete adapters only when live fixture execution needs them.
- Existing adapter conformance reports remain inputs; they are not sufficient for integrated pass unless all three live families contribute refs to one runtime infrastructure report.
- Infrastructure refs do not satisfy publication evidence.
- This feature does not claim managed cloud operations, deployment, production worker fleet, metrics/tracing backend, observability, browser rendering, model SDK, or agent framework readiness.
