"""Live integration tests against real external services.

Every test in this package is gated by ``@pytest.mark.live``. The
default pytest invocation excludes them via the project's
``addopts = "-q -m 'not live'"`` (see ``pyproject.toml``).
Operators run live tests explicitly with ``pytest -m live``;
pytest's CLI ``-m`` replaces the addopts ``-m`` so the override
selects only live tests.

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

Phase 1 step 1.6 was split into sub-steps (reassessment-20260508T091513Z.md):
- 1.6a: httpbin headers — landed in ``test_step_1_6a_httpbin_headers.py``
- 1.6b: httpbin redirect-to — landed in ``test_step_1_6b_httpbin_redirect_to.py``
- 1.6c: example.com — pending
The rest of the live integration tests land in later phases per
design.md §6 step 6.4.
"""
