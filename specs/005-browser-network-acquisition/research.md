# Research: VeraCrawl Browser and Network Acquisition Runtime

## Decision 1: Real HTTP Adapter Uses Standard Library Networking

Use `urllib.request` in `veracrawl.adapters.network.stdlib_http` for the first concrete HTTP adapter.

Rationale:

- It performs real HTTP requests against local deterministic benchmark servers.
- It avoids adding third-party HTTP client coupling while proving the `NetworkClientPort` and `SourceAdapterPort` boundaries.
- It keeps core packages free of concrete networking imports.

Rejected alternatives:

- Add `httpx` or `requests`: useful later, but introduces a concrete dependency before ports/contracts are validated.
- Keep deterministic payloads only: insufficient because this slice must prove real local network acquisition.

## Decision 2: Deterministic Local Benchmark Server Is Test-Owned

Use a test helper server with fixed routes for static HTML, redirect, robots denial, oversized response, slow response, and browser observation fixtures.

Rationale:

- Tests remain deterministic and do not depend on external websites.
- Real socket/network behavior is exercised.
- Policy can explicitly allow loopback only for fixture origins.

## Decision 3: Browser Engine Execution Remains Adapter-Owned

Implement browser observation contracts, sandbox policy gates, deterministic observation adapter, and import-boundary tests now. Do not import Playwright or browser engines into core.

Rationale:

- Target browser capability requires DOM/screenshot/network artifact contracts and safety gates before concrete engines.
- This prevents VeraCrawl from becoming a browser automation demo.
- A later Playwright adapter can satisfy `BrowserObservationPort` without changing contracts.

## Decision 4: Typed Network/Browser Failures Are Non-Success Reports

Treat egress denial, private network denial, robots block, rate budget, size budget, redirect denial, timeout, and unsafe side effect as typed failure reports.

Rationale:

- Operators need visible blocked-source reports.
- Replay can explain why no artifact was accepted.
- Unsafe acquisition cannot be hidden as a transient adapter error.

## Decision 5: Replay Completeness Is Separate From Acquisition Success

Network/browser acquisition can only pass when request, response or browser step, artifact refs, policy refs, source acquisition refs, command refs, event cursor refs, outbox refs, scheduler refs, and durable recovery refs are present.

Rationale:

- Future extraction/evidence layers need source-backed provenance.
- Missing raw HTML, DOM, screenshot, or network metadata must block target-complete claims.
