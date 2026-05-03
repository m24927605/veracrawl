# Research: Real-World Benchmark Corpus Gate

## Decision 1: Treat External Websites As Supplemental Acceptance

Decision: Real-world website runs supplement deterministic fixture/oracle gates and cannot replace them.

Rationale: `docs/11-target-testing-and-acceptance.md` requires synthetic deterministic benchmark sites in CI because public websites can change, rate-limit, or fail independently of VeraCrawl. External runs are still valuable because they prove the live HTTP adapter, policy preflight, artifact creation, and replay refs work outside local fixtures.

Rejected alternative: Make public websites mandatory CI gates. This would make CI flaky and could fail because of third-party downtime instead of product defects.

## Decision 2: Manifest-Driven Corpus, No Site-Specific Scraper

Decision: The benchmark corpus is declared in a manifest and evaluated by generic observations: HTTP status, content type, body size, title fragments, body fragments, and regex counts.

Rationale: The constitution forbids narrowing VeraCrawl into a single-site scraper. Generic observations allow real-site validation without baking in website-specific extraction code.

Rejected alternative: Hard-code Books to Scrape selectors or page-specific extraction. That would prove only a scraper, not a general crawler foundation.

## Decision 3: Robots Preflight And Explicit Origin Allowlist

Decision: Every site must declare its target URL, same-origin robots URL, allowed origins, and permitted robots status codes. Robots 200 responses are parsed with standard robot rules; robots 404 is allowed only when explicitly declared by the manifest.

Rationale: Production-grade external crawling must be governed. Even test/sandbox sites should prove scope and robots handling.

Rejected alternative: Skip robots on demo sites. That would undermine the safety proof and could normalize unsafe crawler behavior.

## Decision 4: Use Existing Live HTTP Runtime

Decision: The real-world benchmark runner composes `execute_live_http_acquisition` and `NetworkSourceAdapterPort` instead of adding a separate fetch path.

Rationale: The benchmark must validate the production spine already built in 039-054: run control, production persistence, source acquisition, artifact refs, command/event/outbox refs, and replay refs.

Rejected alternative: Use raw `urllib` for target pages in the benchmark runner. That would bypass VeraCrawl's acquisition contracts and create a misleading production proof.

## Decision 5: Optional Live Command, Deterministic Tests

Decision: Automated tests use injected adapters and robots fetchers; the live public corpus is run explicitly and recorded in validation results.

Rationale: Unit/contract/integration tests must be reliable offline. The user-requested real crawl proof still needs a real network run, but it should not make every CI run depend on third-party websites.

Rejected alternative: Mark the feature complete after only mocked tests. That would not satisfy the user request to run real websites.
