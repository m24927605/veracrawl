"""Unit tests for ``WorkerPool`` (s17)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from veracrawl.adapters.event_stores.sqlite_event_store import SqliteEventStore
from veracrawl.adapters.work_queue.in_memory_worker_lease import (
    InMemoryWorkerLeaseAdapter,
)
from veracrawl.adapters.work_queue.worker_pool import WorkerPool
from veracrawl.contracts.worker_lease import WorkerLease, WorkOutcome


def _clock() -> datetime:
    return datetime(2026, 5, 15, 12, 0, tzinfo=UTC)


def _always_success(lease: WorkerLease) -> WorkOutcome:
    del lease
    return WorkOutcome(success=True)


def _always_fail(lease: WorkerLease) -> WorkOutcome:
    del lease
    return WorkOutcome(success=False, error_kind="transient")


def _build_pool(
    *,
    work_items: list[str],
    worker_count: int = 2,
    execute_work: object = _always_success,
) -> tuple[WorkerPool, InMemoryWorkerLeaseAdapter, SqliteEventStore]:
    lease_port = InMemoryWorkerLeaseAdapter()
    lease_port.enqueue(work_items)
    outbox = SqliteEventStore()
    pool = WorkerPool(
        pool_id="pool:1",
        worker_count=worker_count,
        lease_port=lease_port,
        outbox_event_store=outbox,
        run_id="run:s17:1",
        execute_work=execute_work,  # type: ignore[arg-type]
        utc_clock=_clock,
        utc_clock_ref="utc-clock:fixture:1",
        budget_ref="budget:1",
    )
    return pool, lease_port, outbox


def test_pool_rejects_invalid_worker_count() -> None:
    lease_port = InMemoryWorkerLeaseAdapter()
    with pytest.raises(ValueError, match="worker_count"):
        WorkerPool(
            pool_id="p", worker_count=0,
            lease_port=lease_port,
            outbox_event_store=SqliteEventStore(),
            run_id="run:1",
            execute_work=_always_success,
            utc_clock=_clock,
            utc_clock_ref="utc-clock:fixture:1",
            budget_ref="budget:1",
        )


def test_pool_rejects_blank_utc_clock_ref() -> None:
    lease_port = InMemoryWorkerLeaseAdapter()
    with pytest.raises(ValueError, match="utc_clock_ref"):
        WorkerPool(
            pool_id="p", worker_count=1,
            lease_port=lease_port,
            outbox_event_store=SqliteEventStore(),
            run_id="run:1",
            execute_work=_always_success,
            utc_clock=_clock,
            utc_clock_ref=" ",
            budget_ref="budget:1",
        )


def test_pool_processes_each_work_item_exactly_once() -> None:
    items = [f"work:{i}" for i in range(10)]
    pool, _, outbox = _build_pool(work_items=items)
    report = pool.run()
    assert report["processed_count"] == 10
    events = outbox.stream("run:s17:1")
    assert len(events) == 10
    # Every work item appears in exactly one outbox event.
    seen_payloads = {e.payload_ref for e in events}
    assert seen_payloads == set(items)


def test_pool_drives_aimd_window_via_success_outcomes() -> None:
    pool, lease_port, _ = _build_pool(
        work_items=[f"work:{i}" for i in range(4)],
        worker_count=1,
        execute_work=_always_success,
    )
    pool.run()
    # 4 successes → window grew from initial_window (1) by +4 = 5.
    assert lease_port.aimd_window_for("worker:pool:1:0") == 5


def test_pool_drives_aimd_window_down_via_failures() -> None:
    pool, lease_port, _ = _build_pool(
        work_items=[f"work:{i}" for i in range(4)],
        worker_count=1,
        execute_work=_always_fail,
    )
    pool.run()
    # initial_window=1; failures → max(1, current//2) = 1 throughout.
    assert lease_port.aimd_window_for("worker:pool:1:0") == 1


def test_pool_outbox_event_types_reflect_outcome_success() -> None:
    pool, _, outbox = _build_pool(
        work_items=["work:1"], worker_count=1, execute_work=_always_success,
    )
    pool.run()
    events = outbox.stream("run:s17:1")
    assert events[0].event_type == "work_item_succeeded"


def test_pool_outbox_event_types_reflect_outcome_failure() -> None:
    pool, _, outbox = _build_pool(
        work_items=["work:1"], worker_count=1, execute_work=_always_fail,
    )
    pool.run()
    events = outbox.stream("run:s17:1")
    assert events[0].event_type == "work_item_failed"


def test_pool_returns_none_for_empty_queue() -> None:
    pool, _, _ = _build_pool(work_items=[], worker_count=2)
    report = pool.run()
    assert report["processed_count"] == 0


def test_pool_deterministic_worker_ids_drive_outbox_actor() -> None:
    pool, _, outbox = _build_pool(
        work_items=["work:1", "work:2"], worker_count=2,
        execute_work=_always_success,
    )
    pool.run()
    events = outbox.stream("run:s17:1")
    actors = {e.actor for e in events}
    assert actors == {"worker:pool:1:0", "worker:pool:1:1"}
