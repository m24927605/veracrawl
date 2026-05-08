"""Live integration tests against real external services.

Every test in this package is gated by ``@pytest.mark.live``. The
default pytest invocation excludes them via the project's
``addopts = "-q"`` plus ``-m 'not live'`` (operators run live
tests explicitly with ``pytest -m live``).

Live tests:
- Hit real network targets (httpbin.org, example.com, eBay official
  API, Amazon SP-API, Cloudflare-protected demo, etc.).
- Validate that the production wiring (real
  :class:`UrllibRobotsParser`, :class:`InMemoryAimdLimiter`,
  :class:`InMemoryConditionalCache`, :class:`InMemoryCookieJar`)
  actually reaches the origin and gets back the expected response.
- Are intentionally fragile: external target drift / provider
  outage / our regression / flake — a live failure must be tagged
  per design.md §6 step 6.5 ``Live failure classification``.

Phase 1 step 1.6 ships live tests #1-#3 (httpbin headers /
redirect-to / example.com); the rest land in later phases.
"""
