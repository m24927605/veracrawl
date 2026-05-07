"""Contract tests for Phase 1 step 1.3 wiring of ``RateLimiterPort``
into ``StdlibHttpSourceAdapter``.

design.md §4 Phase 1 deliverables: cooperative pacing on every HTTP
attempt — initial URL plus every redirect target — with the AIMD
floor sourced from the live ``RobotsAdvice`` so ``Crawl-delay`` /
``Request-rate`` flow into per-request waits.

Boundary acceptance: existing tests must keep passing without any
rate-limiter configuration. The default port is :class:`NoopRateLimiter`,
which is a permissive no-op.

Production gate: under ``RuntimeMode.PRODUCTION``, a default
``NoopRateLimiter`` raises :class:`ProductionRuntimeNotImplemented` so
mis-configured deployments fail closed instead of hammering an origin.
"""

from __future__ import annotations

import httpx
import pytest

from veracrawl.adapters.network.aimd_rate_limiter import InMemoryAimdLimiter
from veracrawl.adapters.network.stdlib_http import (
    HttpClientConfig,
    StdlibHttpSourceAdapter,
)
from veracrawl.contracts.enums import AdapterType, RouteClass
from veracrawl.contracts.network import NetworkRequest
from veracrawl.contracts.source_adapter import SourceAdapterCommand
from veracrawl.fetch.acquisition import source_adapter_spec
from veracrawl.ports.rate_limiter import (
    NoopRateLimiter,
    RateLimiterPort,
    RateLimitFloor,
    RateLimitPermit,
)
from veracrawl.ports.robots import RobotsAdvice
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    with_runtime_mode,
)


def _make_request(url: str = "https://example.test/p/1") -> NetworkRequest:
    return NetworkRequest(
        id="network-request:step-1-3",
        run_ref="run:fixture",
        source_ref=url,
        url=url,
        method="GET",
        headers_ref="headers:step-1-3:request",
        policy_decision_refs=["policy:fixture:default"],
        egress_policy_ref="policy:fixture:egress",
        private_network_policy_ref="policy:fixture:private-network",
        robots_policy_ref="policy:fixture:robots",
        rate_budget_ref="rate:fixture:default",
        size_budget_bytes=1_000_000,
        timeout_ms=10_000,
        idempotency_key="idem:step-1-3",
    )


def _make_command() -> SourceAdapterCommand:
    return SourceAdapterCommand(
        command_envelope_id="cmd:step-1-3",
        adapter_spec=source_adapter_spec(AdapterType.HTTP),
        source_ref="https://example.test/p/1",
        policy_snapshot_ref="policy:fixture:default",
        deterministic_clock_ref="clock:fixture",
        randomness_seed_ref="random:fixture",
    )


def _ok_transport(body: str = "<html>ok</html>") -> httpx.MockTransport:
    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=body.encode("utf-8"), headers={"content-type": "text/html"}
        )

    return httpx.MockTransport(_handler)


def _retry_exhausted_transport() -> httpx.MockTransport:
    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"content-type": "text/plain", "retry-after": "0"})

    return httpx.MockTransport(_handler)


def _redirect_transport(redirects: dict[str, str]) -> httpx.MockTransport:
    def _handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url in redirects:
            return httpx.Response(
                301, headers={"location": redirects[url], "content-type": "text/plain"}
            )
        return httpx.Response(
            200, content=b"<html>ok</html>", headers={"content-type": "text/html"}
        )

    return httpx.MockTransport(_handler)


class _RecordingRateLimiter:
    """Test double — records acquire / report calls without sleeping."""

    def __init__(self, *, throttled_seconds: float | None = None) -> None:
        self.acquired: list[tuple[str, RouteClass, AdapterType, RateLimitFloor | None]] = []
        self.successes: list[RateLimitPermit] = []
        self.throttled: list[tuple[RateLimitPermit, float | None]] = []
        self._throttled_seconds = throttled_seconds

    def acquire(
        self,
        *,
        origin: str,
        route_class: RouteClass,
        adapter_type: AdapterType,
        floor: RateLimitFloor | None = None,
    ) -> RateLimitPermit:
        self.acquired.append((origin, route_class, adapter_type, floor))
        return RateLimitPermit(
            bucket_key=(origin, route_class, adapter_type),
            granted_at_monotonic=0.0,
        )

    def report_success(self, *, permit: RateLimitPermit) -> None:
        permit.mark_reported()
        self.successes.append(permit)

    def report_throttled(
        self,
        *,
        permit: RateLimitPermit,
        retry_after_seconds: float | None = None,
    ) -> None:
        permit.mark_reported()
        self.throttled.append((permit, retry_after_seconds))


def test_recording_limiter_satisfies_runtime_protocol() -> None:
    limiter = _RecordingRateLimiter()
    assert isinstance(limiter, RateLimiterPort)


def test_default_noop_keeps_existing_tests_passing_in_fixture_mode() -> None:
    """Phase 1 boundary acceptance: a fixture-mode adapter built
    without a rate limiter must work — the default ``NoopRateLimiter``
    is permissive in fixture mode."""

    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(),
        transport=_ok_transport(),
    )
    result = adapter.execute(_make_command())
    assert result.status.value == "succeeded"


def test_production_mode_with_default_noop_limiter_fails_closed() -> None:
    """Production mode + default ``NoopRateLimiter`` → fail closed.

    Same pattern as the robots gate: a no-op rate limiter in production
    would skip cooperative pacing, so we refuse to construct.
    """

    from veracrawl.ports.robots import RobotsPort

    class _RealRobots:
        def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
            del url, user_agent
            return RobotsAdvice(is_allowed=True)

    real_robots: RobotsPort = _RealRobots()
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented) as exc:
            StdlibHttpSourceAdapter(
                _make_request(),
                config=HttpClientConfig(robots_port=real_robots),
                transport=_ok_transport(),
            )
    assert exc.value.backend == "rate_limiter"


def test_production_mode_with_real_limiter_succeeds() -> None:
    """Production mode + real limiter succeeds (gate refuses only the
    no-op default)."""

    from veracrawl.ports.robots import RobotsPort

    class _RealRobots:
        def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
            del url, user_agent
            return RobotsAdvice(is_allowed=True)

    real_robots: RobotsPort = _RealRobots()
    real_limiter = InMemoryAimdLimiter()
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = StdlibHttpSourceAdapter(
            _make_request(),
            config=HttpClientConfig(
                robots_port=real_robots,
                rate_limiter=real_limiter,
            ),
            transport=_ok_transport(),
        )
    result = adapter.execute(_make_command())
    assert result.status.value == "succeeded"


def test_adapter_acquires_permit_for_initial_url() -> None:
    limiter = _RecordingRateLimiter()
    adapter = StdlibHttpSourceAdapter(
        _make_request("https://example.test/p/1"),
        config=HttpClientConfig(rate_limiter=limiter),
        transport=_ok_transport(),
    )
    adapter.execute(_make_command())
    assert len(limiter.acquired) == 1
    origin, route, adapter_type, _floor = limiter.acquired[0]
    assert origin == "https://example.test"
    assert route == RouteClass.LISTING
    assert adapter_type == AdapterType.HTTP


def test_adapter_acquires_permit_per_redirect_hop() -> None:
    limiter = _RecordingRateLimiter()
    adapter = StdlibHttpSourceAdapter(
        _make_request("https://example.test/start"),
        config=HttpClientConfig(rate_limiter=limiter, max_redirects=3),
        transport=_redirect_transport(
            {
                "https://example.test/start": "https://example.test/mid",
                "https://example.test/mid": "https://example.test/end",
            }
        ),
    )
    adapter.execute(_make_command())
    # 3 acquires: initial + 2 redirect hops.
    assert len(limiter.acquired) == 3
    assert len(limiter.successes) == 3
    assert limiter.throttled == []


def test_adapter_reports_success_on_2xx() -> None:
    limiter = _RecordingRateLimiter()
    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(rate_limiter=limiter),
        transport=_ok_transport(),
    )
    adapter.execute(_make_command())
    assert len(limiter.successes) == 1
    assert limiter.throttled == []


def test_adapter_reports_throttled_on_retry_exhaustion() -> None:
    """A 429 burst that exhausts retries must report throttle so the
    AIMD bucket halves + applies cooldown for the next caller.
    """

    limiter = _RecordingRateLimiter()
    sleeps: list[float] = []
    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(rate_limiter=limiter, max_attempts=2),
        transport=_retry_exhausted_transport(),
        sleep_fn=sleeps.append,
        jitter_fn=lambda: 0.0,
    )
    from veracrawl.adapters.network.stdlib_http import RetryExhaustedError

    with pytest.raises(RetryExhaustedError):
        adapter.execute(_make_command())
    assert len(limiter.throttled) == 1
    assert limiter.successes == []


def test_floor_passed_through_from_robots_advice() -> None:
    """``Crawl-delay`` / ``Request-rate`` from the robots advice must
    flow into the per-acquire floor so the AIMD limiter sees them.
    """

    from veracrawl.ports.robots import RobotsPort

    class _AdviceRobots:
        def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
            del url, user_agent
            return RobotsAdvice(
                is_allowed=True,
                crawl_delay=4.0,
                request_rate=(1, 2),
            )

    advice_robots: RobotsPort = _AdviceRobots()
    limiter = _RecordingRateLimiter()
    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(robots_port=advice_robots, rate_limiter=limiter),
        transport=_ok_transport(),
    )
    adapter.execute(_make_command())
    assert len(limiter.acquired) == 1
    floor = limiter.acquired[0][3]
    assert floor is not None
    assert floor.crawl_delay_seconds == 4.0
    assert floor.request_rate == (1, 2)


def test_route_class_override_used_in_bucket_key() -> None:
    limiter = _RecordingRateLimiter()
    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(rate_limiter=limiter, route_class=RouteClass.API),
        transport=_ok_transport(),
    )
    adapter.execute(_make_command())
    assert limiter.acquired[0][1] == RouteClass.API


def test_default_noop_limiter_used_when_not_configured() -> None:
    """Construction without a rate limiter falls back to ``NoopRateLimiter``.
    Boundary acceptance: existing tests pass without configuration.
    """

    config = HttpClientConfig()
    assert isinstance(config.rate_limiter, NoopRateLimiter)


class _ProhibitingRateLimiter:
    """Limiter that always raises ``RateLimitProhibited`` on acquire.
    Models the ``Request-rate: 0/N`` floor → infinite-interval case.
    """

    def acquire(
        self,
        *,
        origin: str,
        route_class: RouteClass,
        adapter_type: AdapterType,
        floor: RateLimitFloor | None = None,
    ) -> RateLimitPermit:
        from veracrawl.ports.rate_limiter import RateLimitProhibited

        del route_class, adapter_type, floor
        raise RateLimitProhibited(f"prohibited: {origin}")

    def report_success(self, *, permit: RateLimitPermit) -> None:
        del permit

    def report_throttled(
        self,
        *,
        permit: RateLimitPermit,
        retry_after_seconds: float | None = None,
    ) -> None:
        del permit, retry_after_seconds


def test_rate_limit_prohibited_translates_to_robots_blocked() -> None:
    """When the limiter refuses (e.g. ``Request-rate: 0/N``), the
    adapter must surface a typed cooperative refusal — same shape as
    an explicit ``Disallow`` rule from ``_check_robots``.
    """

    from veracrawl.adapters.network.stdlib_http import RobotsBlockedError

    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(rate_limiter=_ProhibitingRateLimiter()),
        transport=_ok_transport(),
    )
    with pytest.raises(RobotsBlockedError) as exc:
        adapter.execute(_make_command())
    assert "rate-limiter refused" in str(exc.value)


def test_rate_limit_prohibited_with_real_limiter_translates_to_robots_blocked() -> None:
    """End-to-end: real ``InMemoryAimdLimiter`` + robots advice with
    ``request_rate=(0, 60)`` (full prohibition) must surface as
    :class:`RobotsBlockedError` from the HTTP adapter.

    This is the case the contextmanager wrapping makes load-bearing:
    ``RateLimitProhibited`` is raised inside ``acquire``'s generator
    body (which runs on ``__enter__``), so catching it must wrap the
    ``with`` statement, not the bare ``acquire(...)`` call.
    """

    from veracrawl.adapters.network.stdlib_http import RobotsBlockedError
    from veracrawl.ports.robots import RobotsPort

    class _ZeroRateRobots:
        def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
            del url, user_agent
            return RobotsAdvice(
                is_allowed=True,
                request_rate=(0, 60),  # robots-spec full prohibition
            )

    robots: RobotsPort = _ZeroRateRobots()
    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(
            robots_port=robots,
            rate_limiter=InMemoryAimdLimiter(),
        ),
        transport=_ok_transport(),
    )
    with pytest.raises(RobotsBlockedError) as exc:
        adapter.execute(_make_command())
    assert "rate-limiter refused" in str(exc.value)


class _RetryAfterCapturingLimiter:
    """Records the retry_after_seconds passed to report_throttled."""

    def __init__(self) -> None:
        self.acquired: list[str] = []
        self.throttled_retry_after: list[float | None] = []
        self.successes = 0

    def acquire(
        self,
        *,
        origin: str,
        route_class: RouteClass,
        adapter_type: AdapterType,
        floor: RateLimitFloor | None = None,
    ) -> RateLimitPermit:
        del floor
        self.acquired.append(origin)
        return RateLimitPermit(
            bucket_key=(origin, route_class, adapter_type),
            granted_at_monotonic=0.0,
        )

    def report_success(self, *, permit: RateLimitPermit) -> None:
        permit.mark_reported()
        self.successes += 1

    def report_throttled(
        self,
        *,
        permit: RateLimitPermit,
        retry_after_seconds: float | None = None,
    ) -> None:
        permit.mark_reported()
        self.throttled_retry_after.append(retry_after_seconds)


def _retry_after_transport(retry_after: str) -> httpx.MockTransport:
    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"content-type": "text/plain", "retry-after": retry_after},
        )

    return httpx.MockTransport(_handler)


def test_retry_after_propagated_to_report_throttled() -> None:
    """The server's ``Retry-After`` hint must reach the limiter so the
    cooldown extension honors the spec floor (strictest of
    ``Retry-After`` / ``Crawl-delay`` / ``Request-rate``).
    """

    from veracrawl.adapters.network.stdlib_http import RetryExhaustedError

    limiter = _RetryAfterCapturingLimiter()
    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(rate_limiter=limiter, max_attempts=2),
        transport=_retry_after_transport("7"),
        sleep_fn=lambda _s: None,
        jitter_fn=lambda: 0.0,
    )
    with pytest.raises(RetryExhaustedError):
        adapter.execute(_make_command())
    assert limiter.throttled_retry_after == [7.0]


def test_retry_after_none_when_header_absent_on_429() -> None:
    """If the server's 429 has no Retry-After, ``report_throttled`` is
    called with ``retry_after_seconds=None`` (the limiter falls back
    to its base cooldown)."""

    from veracrawl.adapters.network.stdlib_http import RetryExhaustedError

    limiter = _RetryAfterCapturingLimiter()

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"content-type": "text/plain"})

    adapter = StdlibHttpSourceAdapter(
        _make_request(),
        config=HttpClientConfig(rate_limiter=limiter, max_attempts=2),
        transport=httpx.MockTransport(_handler),
        sleep_fn=lambda _s: None,
        jitter_fn=lambda: 0.0,
    )
    with pytest.raises(RetryExhaustedError):
        adapter.execute(_make_command())
    assert limiter.throttled_retry_after == [None]
