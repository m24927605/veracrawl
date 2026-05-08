"""Live test #1 (Phase 1 step 1.6a) — ``httpbin.org/headers``.

design.md §6 step 6.4 deliverable #1: ``httpbin.org/headers`` —
Chrome UA reaches origin.

Validates that the production HTTP adapter wiring (real robots
parser + AIMD limiter + conditional cache + cookie jar + egress
allowlist + private-network denial) actually reaches a public
test origin under ``RuntimeMode.PRODUCTION``. Drift / outage on
the target is tagged per design.md §6 step 6.5 ``Live failure
classification`` (manual operator review).

Gated by ``@pytest.mark.live``; the project's
``pyproject.toml`` excludes the suite by default. Operators run
it with ``pytest -m live tests/integration/live/``.
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


def _make_command(url: str = "https://httpbin.org/headers") -> SourceAdapterCommand:
    return SourceAdapterCommand(
        command_envelope_id="cmd:live:step-1-6a",
        adapter_spec=source_adapter_spec(AdapterType.HTTP),
        source_ref=url,
        policy_snapshot_ref="policy:live:step-1-6a:default",
        deterministic_clock_ref="clock:live:step-1-6a",
        randomness_seed_ref="random:live:step-1-6a",
    )


_HTTPBIN_ALLOWLIST: frozenset[str] = frozenset({"https://httpbin.org"})


def _real_robots_port() -> UrllibRobotsParser:
    """Build the production robots port with the same egress /
    private-network policy the adapter uses: only ``httpbin.org``
    is allowed, private networks are refused. The robots fetcher
    must follow the same policy as the main fetch path or the
    policy boundary is asymmetric."""

    fetcher = make_httpx_robots_fetcher(
        timeout_s=10.0,
        max_redirects=5,
        egress_allowlist=_HTTPBIN_ALLOWLIST,
        allow_private_network=False,
    )
    return UrllibRobotsParser(fetcher=fetcher)


def _production_config(
    *,
    rate_limiter: InMemoryAimdLimiter | None = None,
    conditional_cache: InMemoryConditionalCache | None = None,
) -> HttpClientConfig:
    """Build the full production wiring for the HTTP adapter.

    tests run under
    ``RuntimeMode.PRODUCTION`` AND with the production egress /
    private-network policy (``egress_allowlist`` set, private
    network denied). Every port is a real impl.
    """

    return HttpClientConfig(
        robots_port=_real_robots_port(),
        # Explicit ``is None`` check, not ``or``: ``InMemoryConditionalCache``
        # defines ``__len__``, so an empty instance is falsy and the
        # ``or`` short-circuit would silently replace it with a fresh
        # one. Same defensive pattern for the rate limiter for
        # symmetry.
        rate_limiter=rate_limiter if rate_limiter is not None else InMemoryAimdLimiter(),
        conditional_cache=(
            conditional_cache if conditional_cache is not None else InMemoryConditionalCache()
        ),
        cookie_jar=InMemoryCookieJar(),
        route_class=RouteClass.LISTING,
        egress_allowlist=_HTTPBIN_ALLOWLIST,
        allow_private_network=False,
    )


@pytest.mark.live
def test_httpbin_headers_chrome_ua_reaches_origin_in_production_mode() -> None:
    """Acceptance (design.md §6 step 6.4 #1): Chrome UA reaches
    origin. Runs under ``RuntimeMode.PRODUCTION`` so any
    production-only wiring regression surfaces here."""

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
    """prove the real AIMD limiter is
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
def test_httpbin_real_conditional_cache_populates_etag() -> None:
    """End-to-end live wiring: a 200 response with an ``ETag``
    header lands in the conditional cache. Validates the cache
    port + adapter wiring against a real origin.

    The 304 short-circuit + ``artifact_ref`` reuse contract is
    asserted in the fixture-mode tests (``test_step_1_5_*.py``)
    via ``MockTransport`` — those have deterministic control
    over the conditional protocol, invariant of the live target's
    ETag-matching quirks (httpbin may quote / transform the tag
    server-side; the round-trip semantics belong in the
    fixture-mode contract suite).
    """

    cache = InMemoryConditionalCache()
    config = _production_config(conditional_cache=cache)
    url = "https://httpbin.org/etag/test-step-1-6a"
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = StdlibHttpSourceAdapter(_make_request(url), config=config)
        adapter.execute(_make_command(url))
        result = adapter.last_result
    assert result is not None
    assert result.response.status_code == 200
    cached = cache.get(run_ref="run:live:step-1-6a", url=url)
    assert cached is not None
    assert cached.etag is not None and cached.etag.strip()
    assert cached.body_bytes
    assert cached.body_artifact_ref
