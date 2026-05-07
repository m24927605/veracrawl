"""Unit tests for ``InMemoryAimdLimiter`` (Phase 1 step 1.3 default).

The production default for ``RateLimiterPort`` enforces:

1. **Floor compliance** — design.md §4 Phase 1 acceptance: a 50-fetch
   run against a fixture host with ``crawl_delay=2s`` produces wall
   time ``≥ 49 × 2s ± 100ms``. We exercise this with an injected
   clock / sleep so the test runs in ``O(microseconds)`` of real
   time, asserting the *simulated* sleep total instead of wall-clock.
2. **Multiplicative decrease** on ``report_throttled`` — the bucket
   rate halves (factor 2 by default) and a cooldown window with
   jitter is applied.
3. **Additive increase** after ``successes_to_additive_increase``
   consecutive ``report_success`` calls — rate increases by the
   additive step toward the configured ceiling.
4. **Per-bucket independence** — buckets keyed by
   ``(origin, route_class, adapter_type)`` have independent state; a
   throttle on one does not slow another.
5. **Per-origin concurrency cap** — the bounded semaphore caps
   concurrent in-flight permits per origin at
   ``max_concurrency_per_origin``.

Time-dependent behavior is exercised with injected ``clock_fn`` /
``sleep_fn`` / ``random_fn`` so the tests are deterministic and don't
spend real wall time waiting for AIMD math to play out.
"""

from __future__ import annotations

import threading

import pytest

from veracrawl.adapters.network.aimd_rate_limiter import InMemoryAimdLimiter
from veracrawl.contracts.enums import AdapterType, RouteClass
from veracrawl.ports.rate_limiter import RateLimitFloor, RateLimitProhibited


class _FakeClock:
    """Deterministic monotonic clock + sleep + random.uniform for tests."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []
        self._uniform_value = 0.0

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        if seconds > 0:
            self.now += seconds

    def uniform(self, low: float, high: float) -> float:
        del low, high
        return self._uniform_value

    def set_uniform(self, value: float) -> None:
        self._uniform_value = value


def _make_limiter(
    fake: _FakeClock,
    **overrides: object,
) -> InMemoryAimdLimiter:
    kwargs: dict[str, object] = {
        "initial_rate_per_second": 1.0,
        "min_rate_per_second": 0.001,
        "max_rate_per_second": 10.0,
        "additive_increase_per_second": 0.5,
        "multiplicative_factor": 2.0,
        "cooldown_seconds": 60.0,
        "cooldown_jitter_seconds": 5.0,
        "successes_to_additive_increase": 10,
        "max_concurrency_per_origin": 4,
        "clock_fn": fake.clock,
        "sleep_fn": fake.sleep,
        "random_fn": fake.uniform,
    }
    kwargs.update(overrides)
    return InMemoryAimdLimiter(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# Construction validation
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "field, value",
    [
        ("initial_rate_per_second", 0.0),
        ("min_rate_per_second", 0.0),
        ("additive_increase_per_second", 0.0),
        ("multiplicative_factor", 1.0),
        ("cooldown_seconds", -1.0),
        ("cooldown_jitter_seconds", -0.1),
        ("successes_to_additive_increase", 0),
        ("max_concurrency_per_origin", 0),
    ],
)
def test_constructor_rejects_non_positive_settings(field: str, value: float) -> None:
    fake = _FakeClock()
    with pytest.raises(ValueError):
        _make_limiter(fake, **{field: value})


def test_constructor_rejects_initial_rate_outside_min_max() -> None:
    fake = _FakeClock()
    with pytest.raises(ValueError):
        _make_limiter(
            fake,
            min_rate_per_second=2.0,
            initial_rate_per_second=1.0,
            max_rate_per_second=10.0,
        )


def test_constructor_rejects_min_rate_above_max_rate() -> None:
    fake = _FakeClock()
    with pytest.raises(ValueError):
        _make_limiter(
            fake,
            min_rate_per_second=5.0,
            max_rate_per_second=1.0,
            initial_rate_per_second=1.0,
        )


# ---------------------------------------------------------------------
# Floor / acceptance: 50-fetch crawl_delay=2s wall time ≥ 49 × 2s
# ---------------------------------------------------------------------


def test_acquire_50_times_with_crawl_delay_2s_yields_98s_simulated() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(fake, initial_rate_per_second=10.0)
    floor = RateLimitFloor(crawl_delay_seconds=2.0)
    for _ in range(50):
        with limiter.acquire(
            origin="https://example.com",
            route_class=RouteClass.LISTING,
            adapter_type=AdapterType.HTTP,
            floor=floor,
        ) as permit:
            limiter.report_success(permit=permit)
    # First grant is at t=0 (no last_grant), the next 49 each wait 2s.
    expected = 49 * 2.0
    assert abs(sum(fake.sleeps) - expected) < 0.001
    # Wall time advances by the same amount under the fake clock.
    assert abs(fake.now - expected) < 0.001


def test_request_rate_floor_dominates_when_stricter_than_aimd() -> None:
    fake = _FakeClock()
    # AIMD wants 1 req/s (1s interval), floor (1/5) wants 5s interval.
    limiter = _make_limiter(fake, initial_rate_per_second=1.0)
    floor = RateLimitFloor(request_rate=(1, 5))
    for _ in range(3):
        with limiter.acquire(
            origin="https://example.com",
            route_class=RouteClass.LISTING,
            adapter_type=AdapterType.HTTP,
            floor=floor,
        ) as permit:
            limiter.report_success(permit=permit)
    # 3 grants, 2 inter-request waits of 5s each.
    assert sum(fake.sleeps) == pytest.approx(10.0, abs=0.001)


def test_aimd_interval_dominates_when_stricter_than_floor() -> None:
    fake = _FakeClock()
    # AIMD wants 0.5 req/s = 2s interval; floor wants 1s.
    limiter = _make_limiter(fake, initial_rate_per_second=0.5)
    floor = RateLimitFloor(crawl_delay_seconds=1.0)
    for _ in range(3):
        with limiter.acquire(
            origin="https://example.com",
            route_class=RouteClass.LISTING,
            adapter_type=AdapterType.HTTP,
            floor=floor,
        ) as permit:
            limiter.report_success(permit=permit)
    assert sum(fake.sleeps) == pytest.approx(4.0, abs=0.001)


def test_first_acquire_no_wait() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(fake)
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) == 0.0


# ---------------------------------------------------------------------
# AIMD math: multiplicative decrease + additive increase
# ---------------------------------------------------------------------


def test_report_throttled_halves_rate_and_sets_cooldown() -> None:
    fake = _FakeClock()
    fake.set_uniform(3.0)  # deterministic jitter
    limiter = _make_limiter(fake, initial_rate_per_second=4.0)
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
    assert limiter.current_rate_per_second(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) == pytest.approx(2.0)
    # Next acquire should be deferred by ~63s (60 base + 3 jitter).
    fake.sleeps.clear()
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) == pytest.approx(63.0, abs=0.001)


def test_report_throttled_retry_after_extends_cooldown() -> None:
    fake = _FakeClock()
    fake.set_uniform(0.0)
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit, retry_after_seconds=120.0)
    fake.sleeps.clear()
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) == pytest.approx(120.0, abs=0.001)


def test_report_throttled_floors_at_min_rate() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(
        fake,
        initial_rate_per_second=0.01,
        min_rate_per_second=0.005,
    )
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
        # Next call would halve again; stays at min.
    rate = limiter.current_rate_per_second(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    )
    assert rate >= 0.005
    # Halving 0.01 → 0.005, which is exactly the floor.
    assert rate == pytest.approx(0.005)


def test_additive_increase_after_n_consecutive_successes() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(
        fake,
        initial_rate_per_second=2.0,
        additive_increase_per_second=0.5,
        successes_to_additive_increase=10,
        max_rate_per_second=10.0,
    )
    bucket = dict(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    )
    # 9 successes — no increase yet.
    for _ in range(9):
        with limiter.acquire(**bucket) as permit:
            limiter.report_success(permit=permit)
    assert limiter.current_rate_per_second(**bucket) == pytest.approx(2.0)
    # 10th success triggers the increase.
    with limiter.acquire(**bucket) as permit:
        limiter.report_success(permit=permit)
    assert limiter.current_rate_per_second(**bucket) == pytest.approx(2.5)


def test_throttle_resets_success_counter() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(
        fake,
        initial_rate_per_second=2.0,
        additive_increase_per_second=0.5,
        successes_to_additive_increase=3,
    )
    bucket = dict(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    )
    for _ in range(2):
        with limiter.acquire(**bucket) as permit:
            limiter.report_success(permit=permit)
    # Throttle resets count → next success doesn't immediately bump.
    with limiter.acquire(**bucket) as permit:
        limiter.report_throttled(permit=permit)
    rate_after_throttle = limiter.current_rate_per_second(**bucket)
    with limiter.acquire(**bucket) as permit:
        limiter.report_success(permit=permit)
    # One success after reset is < threshold; rate unchanged.
    assert limiter.current_rate_per_second(**bucket) == pytest.approx(rate_after_throttle)


def test_additive_increase_capped_at_max_rate() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(
        fake,
        initial_rate_per_second=4.5,
        additive_increase_per_second=1.0,
        successes_to_additive_increase=1,
        max_rate_per_second=5.0,
    )
    bucket = dict(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    )
    for _ in range(5):
        with limiter.acquire(**bucket) as permit:
            limiter.report_success(permit=permit)
    assert limiter.current_rate_per_second(**bucket) == pytest.approx(5.0)


# ---------------------------------------------------------------------
# Per-bucket independence
# ---------------------------------------------------------------------


def test_buckets_independent_per_origin() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    with limiter.acquire(
        origin="https://a.example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
    # b.example.com bucket is fresh — no cooldown.
    fake.sleeps.clear()
    with limiter.acquire(
        origin="https://b.example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) == 0.0


def test_buckets_independent_per_route_class() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
    fake.sleeps.clear()
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.DETAIL,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) == 0.0


def test_buckets_independent_per_adapter_type() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.API,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
    fake.sleeps.clear()
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.API,
        adapter_type=AdapterType.AUTHORIZED_SESSION,
    ):
        pass
    assert sum(fake.sleeps) == 0.0


def test_origin_normalization_treats_case_and_path_as_same_bucket() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    with limiter.acquire(
        origin="https://Example.com/path?x=1",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
    fake.sleeps.clear()
    # Same origin (case-insensitive, ignoring path) — cooldown applies.
    with limiter.acquire(
        origin="https://example.com/other",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) > 0.0


# ---------------------------------------------------------------------
# Concurrency cap (real threads, real semaphore — short test)
# ---------------------------------------------------------------------


def test_concurrency_cap_blocks_excess_acquires_per_origin() -> None:
    # Use a real-ish setup: real time/sleep but tiny intervals.
    limiter = InMemoryAimdLimiter(
        initial_rate_per_second=1000.0,
        min_rate_per_second=1.0,
        max_rate_per_second=1000.0,
        additive_increase_per_second=1.0,
        multiplicative_factor=2.0,
        cooldown_seconds=0.0,
        cooldown_jitter_seconds=0.0,
        successes_to_additive_increase=10,
        max_concurrency_per_origin=2,
    )

    in_flight = 0
    in_flight_lock = threading.Lock()
    observed_max = 0
    observed_max_lock = threading.Lock()
    worker_errors: list[BaseException] = []
    worker_errors_lock = threading.Lock()
    completed = 0
    completed_lock = threading.Lock()
    barrier = threading.Barrier(parties=4)

    def worker() -> None:
        nonlocal in_flight, observed_max, completed
        try:
            barrier.wait()
            with limiter.acquire(
                origin="https://example.com",
                route_class=RouteClass.LISTING,
                adapter_type=AdapterType.HTTP,
            ) as permit:
                with in_flight_lock:
                    in_flight += 1
                    current = in_flight
                with observed_max_lock:
                    if current > observed_max:
                        observed_max = current
                # Hold the permit briefly so peers contend on the semaphore.
                threading.Event().wait(0.05)
                with in_flight_lock:
                    in_flight -= 1
                limiter.report_success(permit=permit)
            with completed_lock:
                completed += 1
        except BaseException as exc:  # noqa: BLE001 — capture for assertion
            with worker_errors_lock:
                worker_errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)
    # Codex iter-1 minor: the original test only checked the
    # observed-max bound, so a deadlock or worker exception would have
    # left ``observed_max <= 2`` and silently passed. Now we assert
    # all four workers completed cleanly and no exceptions slipped.
    assert worker_errors == []
    assert all(not t.is_alive() for t in threads)
    assert completed == 4
    assert observed_max <= 2


def test_infinite_floor_raises_prohibited_before_semaphore_acquire() -> None:
    # Codex iter-1 important: ``RateLimitFloor(request_rate=(0, N))``
    # produces an infinite interval; the limiter must refuse before
    # taking a semaphore slot so a worker cannot hang forever inside
    # ``time.sleep(inf)`` while holding the per-origin slot.
    limiter = InMemoryAimdLimiter(
        initial_rate_per_second=1.0,
        min_rate_per_second=0.1,
        max_rate_per_second=10.0,
        additive_increase_per_second=0.5,
        multiplicative_factor=2.0,
        cooldown_seconds=0.0,
        cooldown_jitter_seconds=0.0,
        successes_to_additive_increase=10,
        max_concurrency_per_origin=1,
    )
    floor = RateLimitFloor(request_rate=(0, 60))
    with pytest.raises(RateLimitProhibited):
        with limiter.acquire(
            origin="https://example.com",
            route_class=RouteClass.LISTING,
            adapter_type=AdapterType.HTTP,
            floor=floor,
        ):
            pass
    # Slot must still be free — verify by acquiring without the floor.
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass


def test_concurrency_slot_released_when_with_block_raises() -> None:
    limiter = InMemoryAimdLimiter(
        initial_rate_per_second=1000.0,
        min_rate_per_second=1.0,
        max_rate_per_second=1000.0,
        additive_increase_per_second=1.0,
        multiplicative_factor=2.0,
        cooldown_seconds=0.0,
        cooldown_jitter_seconds=0.0,
        successes_to_additive_increase=10,
        max_concurrency_per_origin=1,
    )

    class _Boom(Exception):
        pass

    try:
        with limiter.acquire(
            origin="https://example.com",
            route_class=RouteClass.LISTING,
            adapter_type=AdapterType.HTTP,
        ):
            raise _Boom
    except _Boom:
        pass

    # Slot should be free; second acquire must not block.
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass


# ---------------------------------------------------------------------
# Permit-state safety
# ---------------------------------------------------------------------


def test_report_methods_do_not_double_release_permit() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(fake)
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_success(permit=permit)
    # Calling report_* explicitly does not pre-empt the with-block's
    # auto-release; the permit is released exactly once on context exit.
    assert permit.released is True


def test_duplicate_report_success_is_noop() -> None:
    # Codex iter-1 important: a permit's AIMD mutation must fire at
    # most once. Calling ``report_success`` 12 times on the same
    # permit (with threshold=10) must not trigger an additive
    # increase, because only the first call is counted.
    fake = _FakeClock()
    limiter = _make_limiter(
        fake,
        initial_rate_per_second=2.0,
        successes_to_additive_increase=10,
    )
    bucket = dict(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    )
    with limiter.acquire(**bucket) as permit:
        for _ in range(12):
            limiter.report_success(permit=permit)
    # Exactly one success counted; rate unchanged.
    assert limiter.current_rate_per_second(**bucket) == pytest.approx(2.0)


def test_duplicate_report_throttled_is_noop() -> None:
    # Codex iter-1 important: ``report_throttled`` is also one-shot.
    # Two calls on the same permit must halve the rate exactly once.
    fake = _FakeClock()
    fake.set_uniform(0.0)
    limiter = _make_limiter(fake, initial_rate_per_second=4.0)
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
        limiter.report_throttled(permit=permit)
        limiter.report_throttled(permit=permit)
    # Halved exactly once: 4.0 → 2.0 (not 0.5).
    assert limiter.current_rate_per_second(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) == pytest.approx(2.0)


def test_report_throttled_after_report_success_is_noop() -> None:
    # Cross-method one-shot: once ``report_success`` lands, a later
    # ``report_throttled`` on the same permit must not also fire.
    fake = _FakeClock()
    fake.set_uniform(0.0)
    limiter = _make_limiter(
        fake,
        initial_rate_per_second=4.0,
        successes_to_additive_increase=1,
    )
    bucket = dict(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    )
    with limiter.acquire(**bucket) as permit:
        limiter.report_success(permit=permit)
        # Threshold=1 so the success already triggered an additive
        # increase: 4.0 → 4.5. The throttle must be ignored.
        limiter.report_throttled(permit=permit)
    assert limiter.current_rate_per_second(**bucket) == pytest.approx(4.5)


def test_schemeless_origin_with_path_normalizes_to_host() -> None:
    # Codex iter-1 minor: schemeless inputs with paths previously
    # became distinct origins; the limiter would split AIMD state
    # and bypass the per-origin concurrency cap.
    fake = _FakeClock()
    fake.set_uniform(0.0)
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    with limiter.acquire(
        origin="example.com/path?x=1",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
    fake.sleeps.clear()
    # ``example.com/other`` shares the bucket with the throttled one.
    with limiter.acquire(
        origin="example.com/other",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) > 0.0


def test_credentialed_url_strips_userinfo_in_bucket_key() -> None:
    # Codex iter-2 important: a credentialed URL must not produce a
    # separate bucket — that would split AIMD state from the bare
    # origin and risk leaking secrets via bucket-key telemetry. The
    # throttle on ``user:pass@example.com`` must apply to plain
    # ``https://example.com``.
    fake = _FakeClock()
    fake.set_uniform(0.0)
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    with limiter.acquire(
        origin="https://user:pass@example.com/path",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
    fake.sleeps.clear()
    with limiter.acquire(
        origin="https://example.com/other",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) > 0.0


def test_credentialed_url_does_not_appear_in_prohibited_message() -> None:
    fake = _FakeClock()
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    floor = RateLimitFloor(request_rate=(0, 60))
    with pytest.raises(RateLimitProhibited) as exc_info:
        with limiter.acquire(
            origin="https://user:secret@example.com/path",
            route_class=RouteClass.LISTING,
            adapter_type=AdapterType.HTTP,
            floor=floor,
        ):
            pass
    msg = str(exc_info.value)
    assert "user" not in msg
    assert "secret" not in msg
    assert "example.com" in msg


def test_schemeless_credentialed_input_strips_userinfo() -> None:
    fake = _FakeClock()
    fake.set_uniform(0.0)
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    with limiter.acquire(
        origin="user:pw@example.com/path",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
    fake.sleeps.clear()
    # Same host without credentials → same bucket → cooldown applies.
    with limiter.acquire(
        origin="example.com/other",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) > 0.0


def test_explicit_port_preserved_in_bucket_key() -> None:
    fake = _FakeClock()
    fake.set_uniform(0.0)
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    # Different ports are different origins per the URL spec.
    with limiter.acquire(
        origin="https://example.com:8443/path",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
    fake.sleeps.clear()
    # Default-port (https → 443) is a *different* bucket.
    with limiter.acquire(
        origin="https://example.com/other",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) == 0.0


def test_schemeless_does_not_synthesize_scheme() -> None:
    # Schemeless inputs key on bare host so two callers cannot share
    # a bucket because one passed ``http://`` and the other passed
    # ``https://``.
    fake = _FakeClock()
    fake.set_uniform(0.0)
    limiter = _make_limiter(fake, initial_rate_per_second=2.0)
    with limiter.acquire(
        origin="example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ) as permit:
        limiter.report_throttled(permit=permit)
    fake.sleeps.clear()
    # Different scheme is a different origin → no cooldown.
    with limiter.acquire(
        origin="https://example.com",
        route_class=RouteClass.LISTING,
        adapter_type=AdapterType.HTTP,
    ):
        pass
    assert sum(fake.sleeps) == 0.0
