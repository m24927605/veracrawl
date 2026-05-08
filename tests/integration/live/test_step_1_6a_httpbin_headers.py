"""Live test #1 (Phase 1 step 1.6a) — ``httpbin.org/headers``.

design.md §6 step 6.4 deliverable #1: "``httpbin.org/headers`` —
Chrome UA reaches origin."

Validates that the production HTTP adapter wiring (real
:class:`UrllibRobotsParser` + :class:`InMemoryAimdLimiter` +
:class:`InMemoryConditionalCache` + :class:`InMemoryCookieJar`)
actually reaches a public test origin and that the headers we
configured (Chrome User-Agent, ``Accept-Language``) arrive at the
target. ``httpbin.org/headers`` echoes the request headers back
as JSON, so we can assert what the origin saw.

This test is **gated** by ``@pytest.mark.live`` — pytest's
default run excludes it (``-m 'not live'`` per
``pyproject.toml`` ``addopts``). Operators run it explicitly with
``pytest -m live tests/integration/live/``.

Iter1 6-point pre-flight scan applied:

1. **Attacker-controlled inputs**: the target is a public test
   service we don't control. Drift / outage are tagged per
   design.md §6 step 6.5 ``Live failure classification`` (not
   yet implemented at this step; manual operator review for
   now).
2. **Execution timing**: real-network latency is variable. Use
   the adapter's existing 10s timeout default; the test does
   not assert timing.
3. **Concurrency**: single fetch, no concurrency.
4. **Failure modes**: target down → flake (operator decides
   `flake` vs `provider_outage` per the failure-classification
   protocol).
5. **PRODUCTION mode**: tests run under
   ``RuntimeMode.PRODUCTION`` so a production-only wiring
   regression (e.g., a new gate added without test coverage)
   surfaces in the live suite (codex iter-1 important).
6. **API symmetry**: same wiring callers would use in
   production (real ports, no-op evidence store / cookies
   irrelevant for this single read).
"""

from __future__ import annotations

import json

import pytest

from veracrawl.adapters.network.aimd_rate_limiter import InMemoryAimdLimiter
from veracrawl.adapters.network.in_memory_conditional_cache import (
    InMemoryConditionalCache,
)
from veracrawl.adapters.network.in_memory_cookie_jar import InMemoryCookieJar
from veracrawl.adapters.network.stdlib_http import (
    HttpClientConfig,
    StdlibHttpSourceAdapter,
)
from veracrawl.adapters.network.urllib_robots import (
    UrllibRobotsParser,
    make_httpx_robots_fetcher,
)
from veracrawl.contracts.enums import AdapterType, RouteClass
from veracrawl.contracts.network import NetworkRequest
from veracrawl.contracts.source_adapter import SourceAdapterCommand
from veracrawl.fetch.acquisition import source_adapter_spec
from veracrawl.runtime_support.runtime_mode import RuntimeMode, with_runtime_mode


def _make_request(url: str = "https://httpbin.org/headers") -> NetworkRequest:
    return NetworkRequest(
        id="network-request:step-1-6a:httpbin-headers",
        run_ref="run:live:step-1-6a",
        source_ref=url,
        url=url,
        method="GET",
        headers_ref="headers:step-1-6a:request",
        policy_decision_refs=["policy:live:step-1-6a:default"],
        egress_policy_ref="policy:live:step-1-6a:egress",
        private_network_policy_ref="policy:live:step-1-6a:private-network",
        robots_policy_ref="policy:live:step-1-6a:robots",
        rate_budget_ref="rate:live:step-1-6a:default",
        size_budget_bytes=1_000_000,
        timeout_ms=15_000,
        idempotency_key="idem:step-1-6a",
    )


def _make_command() -> SourceAdapterCommand:
    return SourceAdapterCommand(
        command_envelope_id="cmd:live:step-1-6a",
        adapter_spec=source_adapter_spec(AdapterType.HTTP),
        source_ref="https://httpbin.org/headers",
        policy_snapshot_ref="policy:live:step-1-6a:default",
        deterministic_clock_ref="clock:live:step-1-6a",
        randomness_seed_ref="random:live:step-1-6a",
    )


def _real_robots_port() -> UrllibRobotsParser:
    """Build the production robots port with a public-internet egress allowance."""

    fetcher = make_httpx_robots_fetcher(
        timeout_s=10.0,
        max_redirects=5,
        # No egress allowlist for the live test — we accept any
        # origin the test target redirects to (none expected).
        allow_private_network=False,
    )
    return UrllibRobotsParser(fetcher=fetcher)


def _production_config(
    *,
    rate_limiter: InMemoryAimdLimiter | None = None,
) -> HttpClientConfig:
    """Build the full production wiring for the HTTP adapter.

    Codex iter-1 important: tests run under
    ``RuntimeMode.PRODUCTION`` so production-only gates don't
    silently break. Every port is a real impl — robots fetcher,
    AIMD limiter, conditional cache, cookie jar.
    """

    return HttpClientConfig(
        robots_port=_real_robots_port(),
        rate_limiter=rate_limiter or InMemoryAimdLimiter(),
        conditional_cache=InMemoryConditionalCache(),
        cookie_jar=InMemoryCookieJar(),
        route_class=RouteClass.LISTING,
    )


@pytest.mark.live
def test_httpbin_headers_chrome_ua_reaches_origin_in_production_mode() -> None:
    """Acceptance (design.md §6 step 6.4 #1): Chrome UA reaches
    origin. Runs under ``RuntimeMode.PRODUCTION`` so any production-
    only wiring regression surfaces here (codex iter-1 important
    — production-mode lift)."""

    config = _production_config()
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = StdlibHttpSourceAdapter(_make_request(), config=config)
        adapter.execute(_make_command())
    result = adapter.last_result
    assert result is not None
    # httpbin echoes the request headers as JSON in
    # ``{"headers": {"User-Agent": "...", ...}}``.
    payload = json.loads(result.body_text)
    assert "headers" in payload, f"unexpected httpbin shape: {payload}"
    echoed = payload["headers"]
    # Chrome UA: assert ``Chrome`` substring so the test stays
    # robust to version bumps the production default may receive.
    user_agent = echoed.get("User-Agent", "")
    assert "Chrome" in user_agent, f"Chrome UA missing from echoed headers: {user_agent!r}"
    # NetworkClientResult populated end-to-end.
    assert result.response.status_code == 200
    assert result.response.final_url == "https://httpbin.org/headers"
    assert len(result.attempt_evidences) == 1
    ev = result.attempt_evidences[0]
    assert ev.response_status == 200
    assert ev.request_method == "GET"
    assert ev.request_url == "https://httpbin.org/headers"
    assert ev.failure_class is None


@pytest.mark.live
def test_httpbin_real_aimd_limiter_engaged_via_success_count() -> None:
    """Codex iter-1/2 important: prove the real AIMD limiter is
    actually engaged by the live path. Use the non-mutating
    ``success_count_for`` accessor (which returns ``0`` when no
    bucket exists) so a no-op-limiter regression — where
    ``report_success`` is never called — fails this test.

    Two successful fetches → success_count == 2 (under threshold
    10, so no additive-increase reset).
    """

    limiter = InMemoryAimdLimiter(initial_rate_per_second=2.0)
    config = _production_config(rate_limiter=limiter)
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter1 = StdlibHttpSourceAdapter(_make_request(), config=config)
        adapter1.execute(_make_command())
        adapter2 = StdlibHttpSourceAdapter(_make_request(), config=config)
        adapter2.execute(_make_command())
    # Non-mutating read: returns 0 if the bucket was never
    # constructed (no-op limiter regression).
    success_count = limiter.success_count_for(
        origin="https://httpbin.org",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    )
    assert success_count == 2, (
        f"expected limiter.report_success called twice, got success_count={success_count} "
        "(zero would indicate the limiter was bypassed)"
    )


@pytest.mark.live
def test_httpbin_real_conditional_cache_round_trip_with_304_short_circuit() -> None:
    """Codex iter-2 important: a single fetch only proves caching,
    not the conditional-fetch round trip. This test does TWO
    fetches against ``httpbin.org/etag/<v>`` and asserts:

    1. First fetch: 200 response, ETag cached, body artifact_ref
       emitted on the result.
    2. Second fetch: ``If-None-Match`` sent, server returns 304,
       adapter short-circuits to the same body and reuses the
       cached body's ``artifact_ref`` — replay traceability.
    """

    cache = InMemoryConditionalCache()
    config = HttpClientConfig(
        robots_port=_real_robots_port(),
        rate_limiter=InMemoryAimdLimiter(),
        conditional_cache=cache,
        cookie_jar=InMemoryCookieJar(),
    )
    url = "https://httpbin.org/etag/test-step-1-6a"
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter1 = StdlibHttpSourceAdapter(_make_request(url), config=config)
        adapter1.execute(_make_command())
        first_result = adapter1.last_result
        assert first_result is not None
        first_artifact_ref = first_result.artifact_refs[0]
        cached = cache.get(run_ref="run:live:step-1-6a", url=url)
        assert cached is not None
        assert cached.etag is not None and "test-step-1-6a" in cached.etag

        adapter2 = StdlibHttpSourceAdapter(_make_request(url), config=config)
        adapter2.execute(_make_command())
        second_result = adapter2.last_result
        assert second_result is not None
        # Same artifact_ref as the first fetch — replay traceability.
        assert second_result.artifact_refs == [first_artifact_ref]
        # Per-attempt evidence captures the wire 304.
        statuses = [ev.response_status for ev in second_result.attempt_evidences]
        assert 304 in statuses
