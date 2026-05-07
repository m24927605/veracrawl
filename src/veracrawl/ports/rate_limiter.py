"""``RateLimiterPort`` — per-(origin, route_class, adapter_type) AIMD limiter.

Phase 1 step 1.3 introduces a hexagonal port the cooperative HTTP /
browser paths consult before each request to a host. The default
production impl is :class:`InMemoryAimdLimiter`
(``adapters/network/aimd_rate_limiter.py``); the framework default is
:class:`NoopRateLimiter` so existing tests pass without configuration
(Phase 1 boundary acceptance, design.md §4 Phase 1).

Two concerns the port collapses into one surface:

1. **AIMD throughput control** keyed by ``(origin, route_class,
   adapter_type)``. Multiplicative decrease on ``429`` (factor 2,
   cooldown 60s with jitter), additive increase after a configurable
   number of consecutive successes (default 10, per design.md §4
   Phase 1).
2. **Floor** = strictest of ``Retry-After`` / ``Crawl-delay`` /
   ``Request-rate``. The AIMD interval can grow above the floor
   (slower) but never below it — a cooperative crawler must respect
   robot-supplied minimum intervals even when the local AIMD curve
   has converged on something faster.

Concurrency cap (``max_concurrency_per_origin``) is enforced by the
production impl; the port surface itself is acquire-and-report so
callers never juggle a separate semaphore. The :class:`RateLimitPermit`
returned by :meth:`RateLimiterPort.acquire` is a context manager so
the standard idiom is::

    with limiter.acquire(origin=..., route_class=..., adapter_type=...) as permit:
        response = client.fetch(url)
        if response.status == 429:
            limiter.report_throttled(permit=permit, retry_after_seconds=ra)
        else:
            limiter.report_success(permit=permit)

The permit auto-releases its concurrency slot on context exit even if
the caller forgets to ``report_*`` (e.g., on an exception). Reporting
without releasing is intentional so a single permit can be reported
exactly once and the AIMD state stays consistent.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from types import TracebackType
from typing import Protocol, runtime_checkable

from veracrawl.contracts.enums import AdapterType, RouteClass


class RateLimitProhibited(Exception):
    """Raised when the floor signals a full prohibition for the bucket.

    Triggered when :attr:`RateLimitFloor.strictest_interval_seconds`
    is infinite — currently the ``Request-rate: 0/N`` directive,
    which the robots.txt spec interprets as "do not fetch". The
    cooperative crawler must abandon (or re-route) instead of
    sleeping forever; raising lets callers map the failure to a typed
    ``RobotsBlockedError`` / refusal at the adapter layer rather than
    silently hanging a worker.
    """


@dataclass(frozen=True)
class RateLimitFloor:
    """The cooperative-crawler floor for inter-request delay.

    A bucket's effective interval between grants is the maximum of
    the AIMD-derived interval and :attr:`strictest_interval_seconds`,
    so the limiter can be slower than the floor (during cooldown or
    early AIMD convergence) but never faster.

    Attributes:
        crawl_delay_seconds: ``Crawl-delay`` directive value, in
            seconds. ``None`` if the host did not specify one.
        request_rate: ``Request-rate`` directive parsed as
            ``(requests, seconds)``. ``None`` if absent. Converted to
            an interval as ``seconds / requests``.
        retry_after_seconds: ``Retry-After`` value (seconds) from a
            recent throttle response. ``None`` if absent.
    """

    crawl_delay_seconds: float | None = None
    request_rate: tuple[int, int] | None = None
    retry_after_seconds: float | None = None

    @property
    def strictest_interval_seconds(self) -> float:
        """Return the longest (strictest) inter-request interval, in seconds.

        The strictest signal wins because each input represents a
        cooperative-crawler floor: violating any one risks the origin
        treating the run as abusive. ``request_rate`` of ``(0, _)`` —
        nominally "0 requests per N seconds" — is treated as a
        prohibition (interval = ``+inf``) so we don't divide by zero.
        ``request_rate`` of ``(req, 0)`` is a malformed directive and
        is ignored (cannot derive an interval from it).
        """

        candidates: list[float] = [0.0]
        if self.crawl_delay_seconds is not None and self.crawl_delay_seconds > 0:
            candidates.append(self.crawl_delay_seconds)
        if self.request_rate is not None:
            req, secs = self.request_rate
            if req == 0 and secs > 0:
                # "0 requests per N seconds" — full prohibition.
                return float("inf")
            if req > 0 and secs > 0:
                candidates.append(secs / req)
        if self.retry_after_seconds is not None and self.retry_after_seconds > 0:
            candidates.append(self.retry_after_seconds)
        return max(candidates)


@dataclass
class RateLimitPermit:
    """A grant of permission to issue one request to a bucket.

    Holds the bucket key plus a release callback so :meth:`release`
    (or context-manager exit) returns the concurrency slot. The permit
    is one-shot: ``release`` is idempotent (safe to call repeatedly),
    and AIMD-state mutations via ``report_success`` / ``report_throttled``
    are guarded by :meth:`mark_reported` so duplicate report calls on
    the same permit do not double-count successes or repeatedly halve
    the rate. ``mark_reported`` is thread-safe: it returns ``True`` for
    the first caller and ``False`` for every subsequent caller.
    """

    bucket_key: tuple[str, RouteClass, AdapterType]
    granted_at_monotonic: float
    _released: bool = field(default=False, repr=False)
    _reported: bool = field(default=False, repr=False)
    _release_callback: Callable[[], None] | None = field(default=None, repr=False)
    _state_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def release(self) -> None:
        """Return the concurrency slot. Idempotent."""

        with self._state_lock:
            if self._released:
                return
            self._released = True
            callback = self._release_callback
        if callback is not None:
            callback()

    def mark_reported(self) -> bool:
        """Return ``True`` if this caller is the first to report; ``False`` otherwise.

        Used by limiter implementations to make AIMD state mutation
        one-shot: the *first* ``report_success`` / ``report_throttled``
        wins and applies its mutation; subsequent calls observe
        ``False`` and become no-ops. Thread-safe by the permit's
        internal lock.
        """

        with self._state_lock:
            if self._reported:
                return False
            self._reported = True
            return True

    @property
    def released(self) -> bool:
        """Return whether the permit has been released. Thread-safe.

        Codex iter-2 minor: the underlying flag is mutated under
        :attr:`_state_lock`, so reading it without the lock could
        observe a stale value on weak memory orderings. Take the lock
        for a coherent read.
        """

        with self._state_lock:
            return self._released

    @property
    def reported(self) -> bool:
        """Return whether the permit has been reported. Thread-safe."""

        with self._state_lock:
            return self._reported

    def __enter__(self) -> RateLimitPermit:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()


@runtime_checkable
class RateLimiterPort(Protocol):
    """Hexagonal port for cooperative request pacing.

    Implementations must be safe to call from multiple threads against
    the same bucket; the production impl uses per-bucket locks and a
    per-origin :class:`threading.BoundedSemaphore`. ``acquire`` blocks
    the calling thread until a permit can be issued; ``report_success``
    and ``report_throttled`` are non-blocking state mutations.
    """

    def acquire(
        self,
        *,
        origin: str,
        route_class: RouteClass,
        adapter_type: AdapterType,
        floor: RateLimitFloor | None = None,
    ) -> AbstractContextManager[RateLimitPermit]:
        """Block until a permit can be issued for one request to this bucket.

        Returns a context manager whose ``__enter__`` yields a
        :class:`RateLimitPermit`. The concrete implementation may
        return either the permit itself (which is its own context
        manager) or a wrapper — callers should treat the return as
        opaque and use ``with`` to scope the permit.
        """

    def report_success(self, *, permit: RateLimitPermit) -> None:
        """Record a successful request for the bucket the permit names.

        Successive successes drive the additive-increase phase of the
        AIMD: after the configured threshold (default 10) the bucket's
        rate inches up by the additive step (until it hits the
        per-origin cap or the floor — whichever is stricter).
        """

    def report_throttled(
        self,
        *,
        permit: RateLimitPermit,
        retry_after_seconds: float | None = None,
    ) -> None:
        """Record a 429 / throttle for the bucket the permit names.

        Triggers the multiplicative-decrease phase: the bucket's rate
        halves (configurable factor) and a cooldown window with jitter
        is set so subsequent ``acquire`` calls wait. ``retry_after_seconds``
        if provided extends the cooldown to honor the server's hint.
        """


class NoopRateLimiter:
    """Permissive default — every acquire is immediate, no AIMD state.

    Used when no rate limiter is configured (Phase 1 boundary
    acceptance: existing tests pass without configuration). Production
    callers must inject :class:`InMemoryAimdLimiter`; leaving the
    no-op in production is a wiring bug, not a permissive policy.
    """

    def acquire(
        self,
        *,
        origin: str,
        route_class: RouteClass,
        adapter_type: AdapterType,
        floor: RateLimitFloor | None = None,
    ) -> RateLimitPermit:
        del origin, route_class, adapter_type, floor
        return RateLimitPermit(
            bucket_key=("", RouteClass.LISTING, AdapterType.HTTP),
            granted_at_monotonic=0.0,
        )

    def report_success(self, *, permit: RateLimitPermit) -> None:
        # Mark reported so duplicate report calls become no-ops — same
        # one-shot guarantee :class:`InMemoryAimdLimiter` offers.
        # Release stays the caller's responsibility (via the permit's
        # context-manager exit) so the no-op default cannot hide
        # caller lifecycle bugs that would surface in production
        # (codex iter-2 minor).
        permit.mark_reported()

    def report_throttled(
        self,
        *,
        permit: RateLimitPermit,
        retry_after_seconds: float | None = None,
    ) -> None:
        del retry_after_seconds
        permit.mark_reported()


__all__ = [
    "NoopRateLimiter",
    "RateLimitFloor",
    "RateLimitPermit",
    "RateLimitProhibited",
    "RateLimiterPort",
]
