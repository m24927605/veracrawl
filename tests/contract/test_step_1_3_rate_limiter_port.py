"""Contract tests for Phase 1 step 1.3 — ``RateLimiterPort``.

The port enforces cooperative-crawler request pacing keyed by
``(origin, route_class, adapter_type)``. It surfaces three operations:

* :meth:`RateLimiterPort.acquire` blocks until a permit can be issued
  (AIMD-derived inter-request interval + per-origin concurrency slot
  + post-throttle cooldown) and returns a :class:`RateLimitPermit`
  context manager.
* :meth:`RateLimiterPort.report_success` records a successful request
  for the bucket so the AIMD additive-increase phase can fire after
  the configured number of consecutive successes.
* :meth:`RateLimiterPort.report_throttled` records a 429 / throttle
  for the bucket, triggering multiplicative-decrease + cooldown.

The framework default :class:`NoopRateLimiter` is permissive (every
acquire is immediate) so existing tests pass without configuration —
Phase 1 boundary acceptance per design.md §4 Phase 1.

The :class:`RateLimitFloor` aggregates the strictest of
``Retry-After`` / ``Crawl-delay`` / ``Request-rate``; the production
default consumes it as the lower bound on the inter-request interval.
"""

from __future__ import annotations

import math

from veracrawl.contracts.enums import AdapterType, RouteClass
from veracrawl.ports.rate_limiter import (
    NoopRateLimiter,
    RateLimiterPort,
    RateLimitFloor,
    RateLimitPermit,
)


def test_route_class_enum_has_design_values() -> None:
    """Per design.md §6: route class is `listing / detail / search / api / file`."""

    assert RouteClass.LISTING.value == "listing"
    assert RouteClass.DETAIL.value == "detail"
    assert RouteClass.SEARCH.value == "search"
    assert RouteClass.API.value == "api"
    assert RouteClass.FILE.value == "file"


def test_floor_no_signals_yields_zero_interval() -> None:
    floor = RateLimitFloor()
    assert floor.strictest_interval_seconds == 0.0


def test_floor_picks_strictest_signal() -> None:
    # crawl_delay 2s vs request_rate 1/5 (= 5s/req) → strictest is 5s.
    floor = RateLimitFloor(crawl_delay_seconds=2.0, request_rate=(1, 5))
    assert floor.strictest_interval_seconds == 5.0


def test_floor_retry_after_dominates_when_largest() -> None:
    floor = RateLimitFloor(
        crawl_delay_seconds=2.0,
        request_rate=(1, 3),
        retry_after_seconds=30.0,
    )
    assert floor.strictest_interval_seconds == 30.0


def test_floor_zero_request_rate_means_full_prohibition() -> None:
    """``Request-rate: 0/N`` is a robots-spec way of saying 'do not fetch'."""

    floor = RateLimitFloor(request_rate=(0, 60))
    assert math.isinf(floor.strictest_interval_seconds)


def test_floor_malformed_request_rate_is_ignored() -> None:
    # ``(N, 0)`` cannot derive an interval (division by zero); ignored.
    floor = RateLimitFloor(crawl_delay_seconds=1.5, request_rate=(5, 0))
    assert floor.strictest_interval_seconds == 1.5


def test_floor_negative_or_zero_crawl_delay_ignored() -> None:
    # urllib parses Crawl-delay as int; non-positive values are
    # malformed in the spec sense and should not affect the floor.
    floor = RateLimitFloor(crawl_delay_seconds=0.0, retry_after_seconds=2.0)
    assert floor.strictest_interval_seconds == 2.0


def test_permit_release_is_idempotent() -> None:
    calls: list[None] = []
    permit = RateLimitPermit(
        bucket_key=("origin", RouteClass.LISTING, AdapterType.HTTP),
        granted_at_monotonic=0.0,
        _release_callback=lambda: calls.append(None),
    )
    assert permit.released is False
    permit.release()
    permit.release()
    assert permit.released is True
    assert len(calls) == 1


def test_permit_context_manager_releases_on_exit() -> None:
    calls: list[None] = []
    permit = RateLimitPermit(
        bucket_key=("origin", RouteClass.LISTING, AdapterType.HTTP),
        granted_at_monotonic=0.0,
        _release_callback=lambda: calls.append(None),
    )
    with permit:
        assert permit.released is False
    assert permit.released is True
    assert len(calls) == 1


def test_permit_context_manager_releases_on_exception() -> None:
    calls: list[None] = []
    permit = RateLimitPermit(
        bucket_key=("origin", RouteClass.LISTING, AdapterType.HTTP),
        granted_at_monotonic=0.0,
        _release_callback=lambda: calls.append(None),
    )

    class _Boom(Exception):
        pass

    try:
        with permit:
            raise _Boom
    except _Boom:
        pass
    assert permit.released is True
    assert len(calls) == 1


def test_noop_limiter_grants_immediately_and_satisfies_protocol() -> None:
    limiter: RateLimiterPort = NoopRateLimiter()
    permit = limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    )
    assert isinstance(permit, RateLimitPermit)
    limiter.report_success(permit=permit)
    assert permit.released is True


def test_noop_limiter_report_throttled_releases_permit() -> None:
    limiter = NoopRateLimiter()
    permit = limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    )
    limiter.report_throttled(permit=permit, retry_after_seconds=12.0)
    assert permit.released is True


def test_noop_limiter_satisfies_runtime_protocol() -> None:
    limiter = NoopRateLimiter()
    assert isinstance(limiter, RateLimiterPort)
