"""s17 live integration test: ``MultiprocessWorkerPool`` actually spawns processes.

Closes carry-forward gap #4. Marked ``@pytest.mark.live`` because
``multiprocessing.get_context('spawn')`` workers have ~100ms startup
overhead each and the test takes ~1-3 seconds total. Hidden behind
the live mark so the default ``-m "not live"`` pytest run stays
fast; runs in CI under ``-m live``.

The execute callable lives at module-top-level in
``_multiprocess_worker_fixtures.py`` (closures can't be pickled
across spawn boundaries).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from veracrawl.adapters.event_stores.sqlite_event_store import SqliteEventStore
from veracrawl.adapters.work_queue.in_memory_worker_lease import (
    InMemoryWorkerLeaseAdapter,
)
from veracrawl.adapters.work_queue.multiprocess_worker_pool import (
    MultiprocessWorkerPool,
)


def _clock() -> datetime:
    return datetime(2026, 5, 16, 12, 0, tzinfo=UTC)


pytestmark = pytest.mark.live


def test_multiprocess_pool_processes_each_work_item_exactly_once() -> None:
    """2-process pool against 10 work items. Verifies every item is
    processed exactly once and every outcome lands in the outbox.
    """

    items = [f"work:multi:{i}" for i in range(10)]
    lease_port = InMemoryWorkerLeaseAdapter()
    lease_port.enqueue(items)
    outbox = SqliteEventStore()
    pool = MultiprocessWorkerPool(
        pool_id="multi:1",
        worker_count=2,
        lease_port=lease_port,
        outbox_event_store=outbox,
        run_id="run:s17:multi:1",
        execute_reference=(
            "tests.integration._multiprocess_worker_fixtures:echo_success"
        ),
        utc_clock=_clock,
        utc_clock_ref="utc-clock:fixture:1",
        budget_ref="budget:multi",
    )
    report = pool.run()
    assert report["processed_count"] == 10
    events = outbox.stream("run:s17:multi:1")
    assert len(events) == 10
    seen_refs = {e.payload_ref for e in events}
    assert seen_refs == set(items)


def test_multiprocess_pool_outbox_event_types_reflect_outcome() -> None:
    """Worker outcomes propagate to ``CrawlRunEvent.event_type`` correctly."""

    items = [f"work:multi:fail:{i}" for i in range(4)]
    lease_port = InMemoryWorkerLeaseAdapter()
    lease_port.enqueue(items)
    outbox = SqliteEventStore()
    pool = MultiprocessWorkerPool(
        pool_id="multi:fail",
        worker_count=2,
        lease_port=lease_port,
        outbox_event_store=outbox,
        run_id="run:s17:multi:fail",
        execute_reference=(
            "tests.integration._multiprocess_worker_fixtures:echo_failure"
        ),
        utc_clock=_clock,
        utc_clock_ref="utc-clock:fixture:1",
        budget_ref="budget:multi",
    )
    pool.run()
    events = outbox.stream("run:s17:multi:fail")
    event_types = {e.event_type for e in events}
    assert event_types == {"work_item_failed"}


def test_multiprocess_pool_empty_queue_short_circuits() -> None:
    """No work → no subprocess spawn, no outbox events."""

    lease_port = InMemoryWorkerLeaseAdapter()
    outbox = SqliteEventStore()
    pool = MultiprocessWorkerPool(
        pool_id="multi:empty",
        worker_count=2,
        lease_port=lease_port,
        outbox_event_store=outbox,
        run_id="run:s17:multi:empty",
        execute_reference=(
            "tests.integration._multiprocess_worker_fixtures:echo_success"
        ),
        utc_clock=_clock,
        utc_clock_ref="utc-clock:fixture:1",
        budget_ref="budget:multi",
    )
    report = pool.run()
    assert report["processed_count"] == 0
    assert report["outbox_event_count"] == 0


def test_multiprocess_pool_rejects_invalid_execute_reference() -> None:
    """Ctor validates the ``module:qualname`` shape."""

    lease_port = InMemoryWorkerLeaseAdapter()
    outbox = SqliteEventStore()
    with pytest.raises(ValueError, match="execute_reference"):
        MultiprocessWorkerPool(
            pool_id="x", worker_count=1,
            lease_port=lease_port, outbox_event_store=outbox,
            run_id="run:x",
            execute_reference="no_colon_in_this_one",
            utc_clock=_clock, utc_clock_ref="utc-clock:1",
            budget_ref="budget:x",
        )
