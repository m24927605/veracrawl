# Research: JavaScript Browser Crawl Quality Benchmark

## Decision: Browser Quality Composes HTTP-Only And Browser Observations

- **Decision**: Each target first runs an HTTP-only observation, then a browser
  observation only when policy, egress, sandbox, and budget allow it. The
  quality report compares oracle fragments recovered by browser rendering
  against fragments missing from HTTP-only evidence.
- **Rationale**: The benchmark must prove browser rendering improved evidence,
  not merely that a browser step executed.
- **Rejected**: Running only browser observation was rejected because it cannot
  prove differential quality gain.

## Decision: Core Depends On Browser Port, Not Playwright

- **Decision**: `veracrawl.benchmarks.browser_quality` accepts HTTP and browser
  adapter factories through VeraCrawl ports. Playwright is implemented only in
  `veracrawl.adapters.browser.playwright` and loaded by the CLI when requested.
- **Rationale**: This preserves the constitution boundary that browser engines
  are adapter-owned and replaceable.
- **Rejected**: Importing Playwright in runtime/contracts was rejected because
  it would couple core to a browser engine and framework-native state.

## Decision: Passing Browser Evidence Requires Text Anchors And Hashes

- **Decision**: A recovered oracle fragment must produce a source anchor ref and
  a rendered content hash ref. DOM and screenshots alone cannot satisfy a
  recovered evidence claim.
- **Rationale**: Screenshots are useful artifacts but are not enough to support
  machine-auditable text evidence and replay.
- **Rejected**: Accepting screenshots without anchors was rejected as
  non-verifiable.

## Decision: Live Validation Uses Stable Public JS Targets

- **Decision**: The quality profile includes at least eight public JS-rendered
  targets. The deterministic fixture tests can monkeypatch adapters, but the
  recorded live CLI validation must use the Playwright adapter and real public
  URLs.
- **Rationale**: Local fixtures prove negative and replay behavior; a live run
  proves the adapter can render public JS pages.
- **Rejected**: Calling deterministic browser refs a live browser pass was
  rejected as deceptive.

## Decision: Unsafe Browser Behavior Is Typed And Blocking

- **Decision**: unsafe action class, prompt-tainted instruction bypass, missing
  artifacts/anchors, budget exhaustion, and replay mismatch each produce typed
  `BrowserQualityFailureType` diagnostics and a failing report.
- **Rationale**: Browser execution is high-risk and must fail visibly.
- **Rejected**: Silent downgrade to HTTP-only was rejected because it can hide
  missing JS-required evidence.

## Decision: Optional Browser Dependency

- **Decision**: Add an optional `browser-playwright` extra for live browser
  validation. Default dev/full tests remain runnable without browser engine
  installation by using fixture adapters.
- **Rationale**: CI and local development should not require a browser download
  unless the live browser gate is explicitly invoked.
- **Rejected**: Making Playwright a required dependency was rejected because it
  would slow unrelated tests and create an unnecessary browser engine dependency
  for core users.
