"""``InMemoryAimdLimiter`` — production default for ``RateLimiterPort``.

Implements the AIMD discipline design.md §4 Phase 1 calls for:

* **Per-(origin, route_class, adapter_type) bucket.** Independent
  state per tuple so a 429 against ``listing`` doesn't slow ``api``
  on the same origin (and vice-versa).
* **Multiplicative decrease** on each ``report_throttled``: the
  bucket's rate is divided by ``multiplicative_factor`` (default 2)
  and a cooldown window of
  ``cooldown_seconds + uniform(0, cooldown_jitter_seconds)`` is set.
  Cooldown jitter prevents thundering-herd retries when many workers
  hit the same 429 simultaneously.
* **Additive increase** after ``successes_to_additive_increase``
  consecutive ``report_success`` calls (default 10). The rate inches
  up by ``additive_increase_per_second`` until it hits
  ``max_rate_per_second``.
* **Floor.** ``RateLimitFloor.strictest_interval_seconds`` (the
  strictest of ``Retry-After`` / ``Crawl-delay`` / ``Request-rate``)
  is the lower bound on the inter-request interval. The AIMD-derived
  interval is allowed to be slower than the floor (during cooldown
  or before convergence) but never faster.
* **Per-origin concurrency cap.** A
  :class:`threading.BoundedSemaphore` per origin enforces
  ``max_concurrency_per_origin`` (default 4); :meth:`acquire` blocks
  on it before any AIMD math. The slot is released when the
  :class:`RateLimitPermit` exits its context (or :meth:`release` is
  called directly).

Determinism for tests is exposed via ``clock_fn`` / ``sleep_fn`` /
``random_fn`` injection — the same pattern Phase 1 step 1.2 used for
``UrllibRobotsParser``. With the defaults the limiter uses
``time.monotonic`` / ``time.sleep`` / ``random.uniform``.

The limiter is intentionally synchronous; cooperative crawl loops
and the rendering path are sync today (Phase 1 scope). An async port
can be layered on later without changing the contract surface.
"""

from __future__ import annotations

import math
import random
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Final
from urllib.parse import urlsplit

from veracrawl.contracts.enums import AdapterType, RouteClass
from veracrawl.ports.rate_limiter import (
    RateLimitFloor,
    RateLimitPermit,
    RateLimitProhibited,
)
from veracrawl.runtime_support.logging import get_logger

_logger = get_logger(__name__)

_DEFAULT_INITIAL_RATE_PER_SECOND: Final[float] = 1.0
_DEFAULT_MAX_RATE_PER_SECOND: Final[float] = 10.0
_DEFAULT_MIN_RATE_PER_SECOND: Final[float] = 1e-3
_DEFAULT_ADDITIVE_INCREASE_PER_SECOND: Final[float] = 0.5
_DEFAULT_MULTIPLICATIVE_FACTOR: Final[float] = 2.0
_DEFAULT_COOLDOWN_SECONDS: Final[float] = 60.0
_DEFAULT_COOLDOWN_JITTER_SECONDS: Final[float] = 5.0
_DEFAULT_SUCCESSES_TO_INCREASE: Final[int] = 10
_DEFAULT_MAX_CONCURRENCY_PER_ORIGIN: Final[int] = 4


@dataclass
class _BucketState:
    """Mutable AIMD state for one ``(origin, route_class, adapter_type)``.

    Protected by :attr:`lock`; all reads / writes from outside the
    bucket take the lock briefly. ``acquire`` may sleep without
    holding the lock and re-checks state on each wakeup so concurrent
    acquires on the same bucket end up properly spaced (the loser of
    a race observes the winner's updated ``last_grant_monotonic`` and
    waits again).
    """

    rate_per_second: float
    success_count: int = 0
    last_grant_monotonic: float | None = None
    cooldown_until_monotonic: float | None = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


class InMemoryAimdLimiter:
    """``RateLimiterPort`` impl with AIMD + cooldown + per-origin cap.

    Construction parameters (all keyword-only):

    * ``initial_rate_per_second``: starting rate for fresh buckets
      (default 1 req/s — conservative for a cooperative crawler).
    * ``min_rate_per_second`` / ``max_rate_per_second``: AIMD floor /
      ceiling for the rate (the inter-request interval is the
      reciprocal). The :class:`RateLimitFloor` per-acquire signal
      tightens these further at request time.
    * ``additive_increase_per_second``: rate added after every
      ``successes_to_additive_increase`` consecutive successes.
    * ``multiplicative_factor``: divisor applied on each
      ``report_throttled``.
    * ``cooldown_seconds`` / ``cooldown_jitter_seconds``: post-throttle
      cooldown base + uniform jitter window. Jitter avoids
      thundering-herd retries when many workers hit the same 429.
    * ``successes_to_additive_increase``: consecutive successes
      required before the next additive-increase tick.
    * ``max_concurrency_per_origin``: per-origin
      :class:`threading.BoundedSemaphore` cap (default 4).
    * ``clock_fn`` / ``sleep_fn`` / ``random_fn``: injection points for
      tests. Defaults are ``time.monotonic`` / ``time.sleep`` /
      ``random.uniform``.
    """

    def __init__(
        self,
        *,
        initial_rate_per_second: float = _DEFAULT_INITIAL_RATE_PER_SECOND,
        min_rate_per_second: float = _DEFAULT_MIN_RATE_PER_SECOND,
        max_rate_per_second: float = _DEFAULT_MAX_RATE_PER_SECOND,
        additive_increase_per_second: float = _DEFAULT_ADDITIVE_INCREASE_PER_SECOND,
        multiplicative_factor: float = _DEFAULT_MULTIPLICATIVE_FACTOR,
        cooldown_seconds: float = _DEFAULT_COOLDOWN_SECONDS,
        cooldown_jitter_seconds: float = _DEFAULT_COOLDOWN_JITTER_SECONDS,
        successes_to_additive_increase: int = _DEFAULT_SUCCESSES_TO_INCREASE,
        max_concurrency_per_origin: int = _DEFAULT_MAX_CONCURRENCY_PER_ORIGIN,
        clock_fn: Callable[[], float] = time.monotonic,
        sleep_fn: Callable[[float], None] = time.sleep,
        random_fn: Callable[[float, float], float] = random.uniform,
    ) -> None:
        if initial_rate_per_second <= 0:
            raise ValueError("initial_rate_per_second must be positive")
        if min_rate_per_second <= 0:
            raise ValueError("min_rate_per_second must be positive")
        if max_rate_per_second < min_rate_per_second:
            raise ValueError("max_rate_per_second must be >= min_rate_per_second")
        if not (min_rate_per_second <= initial_rate_per_second <= max_rate_per_second):
            raise ValueError("initial_rate_per_second must be between min and max rate")
        if additive_increase_per_second <= 0:
            raise ValueError("additive_increase_per_second must be positive")
        if multiplicative_factor <= 1:
            raise ValueError("multiplicative_factor must be > 1")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be non-negative")
        if cooldown_jitter_seconds < 0:
            raise ValueError("cooldown_jitter_seconds must be non-negative")
        if successes_to_additive_increase <= 0:
            raise ValueError("successes_to_additive_increase must be positive")
        if max_concurrency_per_origin <= 0:
            raise ValueError("max_concurrency_per_origin must be positive")
        self._initial_rate = initial_rate_per_second
        self._min_rate = min_rate_per_second
        self._max_rate = max_rate_per_second
        self._additive = additive_increase_per_second
        self._md_factor = multiplicative_factor
        self._cooldown_base = cooldown_seconds
        self._cooldown_jitter = cooldown_jitter_seconds
        self._successes_threshold = successes_to_additive_increase
        self._max_concurrency = max_concurrency_per_origin
        self._clock = clock_fn
        self._sleep = sleep_fn
        self._random = random_fn

        self._registry_lock = threading.Lock()
        self._buckets: dict[tuple[str, RouteClass, AdapterType], _BucketState] = {}
        self._semaphores: dict[str, threading.BoundedSemaphore] = {}

    # -- Public API ---------------------------------------------------

    @contextmanager
    def acquire(
        self,
        *,
        origin: str,
        route_class: RouteClass,
        adapter_type: AdapterType,
        floor: RateLimitFloor | None = None,
    ) -> Iterator[RateLimitPermit]:
        """Block until a permit can be issued; auto-release on context exit.

        See :class:`~veracrawl.ports.rate_limiter.RateLimiterPort`.
        """

        normalized_origin = _normalize_origin(origin)
        bucket_key = (normalized_origin, route_class, adapter_type)
        # Refuse the request before acquiring a semaphore slot when
        # the floor signals a full prohibition (``Request-rate: 0/N``
        # → infinite interval). Sleeping forever would hang a worker
        # and strand the per-origin slot. The exception uses the
        # *normalized* origin so credentials a caller smuggled into
        # the raw URL cannot leak via the message.
        if floor is not None and not _is_finite_interval(floor.strictest_interval_seconds):
            raise RateLimitProhibited(
                f"floor signals full prohibition for origin {normalized_origin!r}"
            )
        sem = self._semaphore_for(normalized_origin)
        sem.acquire()
        permit_released = threading.Event()

        def _release_once() -> None:
            if permit_released.is_set():
                return
            permit_released.set()
            sem.release()

        try:
            granted_at = self._wait_for_grant(bucket_key=bucket_key, floor=floor)
            permit = RateLimitPermit(
                bucket_key=bucket_key,
                granted_at_monotonic=granted_at,
                _release_callback=_release_once,
            )
            try:
                yield permit
            finally:
                permit.release()
        except BaseException:
            # If we never built a permit (waited and the caller errored,
            # or the with-block raised before yield), release the
            # concurrency slot so a hung sem.acquire doesn't strand the
            # origin. ``_release_once`` is idempotent.
            _release_once()
            raise

    def report_success(self, *, permit: RateLimitPermit) -> None:
        # AIMD state mutation is one-shot per permit. ``mark_reported``
        # returns ``True`` only for the first caller; duplicate reports
        # become no-ops so the success counter cannot be inflated and
        # an additive-increase tick cannot fire spuriously.
        if not permit.mark_reported():
            return
        bucket = self._lookup_bucket(permit.bucket_key)
        if bucket is None:
            return
        with bucket.lock:
            bucket.success_count += 1
            if bucket.success_count >= self._successes_threshold:
                bucket.success_count = 0
                bucket.rate_per_second = min(
                    self._max_rate,
                    bucket.rate_per_second + self._additive,
                )

    def report_throttled(
        self,
        *,
        permit: RateLimitPermit,
        retry_after_seconds: float | None = None,
    ) -> None:
        # Same one-shot guarantee as ``report_success`` — duplicate
        # reports must not stack multiplicative decreases or repeatedly
        # extend the cooldown.
        if not permit.mark_reported():
            return
        bucket = self._lookup_bucket(permit.bucket_key)
        if bucket is None:
            return
        with bucket.lock:
            new_rate = max(
                self._min_rate,
                bucket.rate_per_second / self._md_factor,
            )
            bucket.rate_per_second = new_rate
            bucket.success_count = 0
            now = self._clock()
            jitter = self._random(0.0, self._cooldown_jitter) if self._cooldown_jitter > 0 else 0.0
            cooldown_candidate = now + self._cooldown_base + jitter
            if retry_after_seconds is not None and retry_after_seconds > 0:
                cooldown_candidate = max(cooldown_candidate, now + retry_after_seconds)
            existing = bucket.cooldown_until_monotonic
            cooldown_until = (
                cooldown_candidate if existing is None else max(existing, cooldown_candidate)
            )
            bucket.cooldown_until_monotonic = cooldown_until
        origin, route_class, adapter_type = permit.bucket_key
        _logger.info(
            "rate_limiter_throttled",
            origin=origin,
            route_class=route_class.value,
            adapter_type=adapter_type.value,
            new_rate_per_second=new_rate,
            cooldown_seconds=cooldown_until - now,
            retry_after_seconds=retry_after_seconds,
        )

    # -- Inspection (test / observability) ---------------------------

    def current_rate_per_second(
        self,
        *,
        origin: str,
        route_class: RouteClass,
        adapter_type: AdapterType,
    ) -> float:
        """Return the current rate for a bucket (creates it on first read)."""

        bucket = self._get_or_create_bucket((_normalize_origin(origin), route_class, adapter_type))
        with bucket.lock:
            return bucket.rate_per_second

    def success_count_for(
        self,
        *,
        origin: str,
        route_class: RouteClass,
        adapter_type: AdapterType,
    ) -> int:
        """Return the success counter for the bucket; ``0`` if the
        bucket has never been touched.

        Non-mutating: unlike :meth:`current_rate_per_second`, this
        accessor does NOT create the bucket on first read. Used by
        live tests to verify the limiter's ``report_success`` was
        actually called by the adapter (a no-op limiter would never
        construct a bucket; success_count_for returns ``0`` and
        the test fails).
        """

        key = (_normalize_origin(origin), route_class, adapter_type)
        bucket = self._lookup_bucket(key)
        if bucket is None:
            return 0
        with bucket.lock:
            return bucket.success_count

    # -- Internals ---------------------------------------------------

    def _semaphore_for(self, origin: str) -> threading.BoundedSemaphore:
        with self._registry_lock:
            sem = self._semaphores.get(origin)
            if sem is None:
                sem = threading.BoundedSemaphore(self._max_concurrency)
                self._semaphores[origin] = sem
            return sem

    def _get_or_create_bucket(self, key: tuple[str, RouteClass, AdapterType]) -> _BucketState:
        with self._registry_lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = _BucketState(rate_per_second=self._initial_rate)
                self._buckets[key] = bucket
            return bucket

    def _lookup_bucket(self, key: tuple[str, RouteClass, AdapterType]) -> _BucketState | None:
        with self._registry_lock:
            return self._buckets.get(key)

    def _wait_for_grant(
        self,
        *,
        bucket_key: tuple[str, RouteClass, AdapterType],
        floor: RateLimitFloor | None,
    ) -> float:
        bucket = self._get_or_create_bucket(bucket_key)
        floor_interval = floor.strictest_interval_seconds if floor is not None else 0.0
        # Loop with re-check: two threads racing for the same bucket
        # both observe the same wait, both sleep, both wake; whichever
        # wins the bucket lock writes ``last_grant_monotonic`` and the
        # loser observes it on its next iteration and waits again.
        while True:
            with bucket.lock:
                now = self._clock()
                aimd_interval = 1.0 / max(bucket.rate_per_second, self._min_rate)
                effective_interval = max(floor_interval, aimd_interval)
                target = now
                if bucket.last_grant_monotonic is not None:
                    target = max(target, bucket.last_grant_monotonic + effective_interval)
                if bucket.cooldown_until_monotonic is not None:
                    target = max(target, bucket.cooldown_until_monotonic)
                wait = target - now
                if wait <= 0.0:
                    bucket.last_grant_monotonic = now
                    return now
            self._sleep(wait)


def _normalize_origin(origin: str) -> str:
    """Lowercase scheme+host[:port], strip path/query/fragment + userinfo.

    The bucket key is the origin, not the URL — two URLs on the same
    host share the bucket. We accept either a bare ``host``, a
    ``scheme://host`` origin, or a full URL and reduce them to the
    canonical ``scheme://host[:port]`` form for keying.

    Userinfo (``user:pass@``) is dropped explicitly. Building from
    ``parts.netloc`` would preserve userinfo and a caller passing
    ``https://user:pass@example.com/path`` would key a separate bucket
    containing credentials — splitting rate-limit / concurrency
    state from ``https://example.com`` and risking secret exposure in
    error messages or telemetry. We rebuild the netloc from
    ``parts.hostname`` (already lowercased, userinfo stripped) plus
    the explicit port, never trusting ``parts.netloc`` as-is.

    Schemeless inputs (``example.com``, ``example.com/path?x=1``) are
    interpreted host-first: the host is the substring up to the first
    ``/``, ``?`` or ``#``, then any leading ``user:pass@`` is peeled
    off (a schemeless input can smuggle userinfo too — same hygiene
    applies). Without this normalization, paths under the same host
    became distinct origins and would silently split AIMD state +
    bypass the per-origin concurrency cap. We never synthesise a
    scheme the caller did not provide.
    """

    if not origin:
        return ""
    parts = urlsplit(origin)
    if parts.scheme and parts.hostname:
        host = parts.hostname  # already lowercased; userinfo stripped
        try:
            port = parts.port
        except ValueError:
            # Malformed port — keep the userinfo strip applied. Falling
            # back to ``origin.lower()`` would have leaked credentials
            # through bucket keys, telemetry, and ``RateLimitProhibited``
            # error messages for inputs like
            # ``https://user:secret@example.com:bad/path``. Build the
            # safe form from ``parts.scheme`` + ``parts.hostname`` and
            # surface the malformed port as a raw token so callers can
            # see something is off, but never as part of a credential-
            # bearing string.
            return f"{parts.scheme.lower()}://{host}:<malformed-port>"
        if port is not None:
            return f"{parts.scheme.lower()}://{host}:{port}"
        return f"{parts.scheme.lower()}://{host}"
    # Schemeless: split host from any path/query/fragment first…
    schemeless = origin.lower()
    for sep in ("/", "?", "#"):
        idx = schemeless.find(sep)
        if idx >= 0:
            schemeless = schemeless[:idx]
    # …then strip leading ``user:pass@`` (defence in depth: a
    # schemeless input that smuggled userinfo must not key a
    # credential-bearing bucket either).
    at_idx = schemeless.rfind("@")
    if at_idx >= 0:
        schemeless = schemeless[at_idx + 1 :]
    return schemeless


def _is_finite_interval(seconds: float) -> bool:
    """Return ``True`` if ``seconds`` is a finite, non-NaN number."""

    return math.isfinite(seconds)


__all__ = ["InMemoryAimdLimiter"]
