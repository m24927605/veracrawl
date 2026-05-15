"""Unit tests for ``InMemoryWorkerLeaseAdapter`` (s16)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from veracrawl.adapters.work_queue.in_memory_worker_lease import (
    InMemoryWorkerLeaseAdapter,
)
from veracrawl.contracts.worker_lease import WorkOutcome
from veracrawl.ports.worker_lease import WorkerLeasePort

_T = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)


def _fixed_clock() -> datetime:
    return _T


def test_adapter_implements_worker_lease_port() -> None:
    assert isinstance(InMemoryWorkerLeaseAdapter(), WorkerLeasePort)


def test_acquire_returns_none_when_queue_empty() -> None:
    adapter = InMemoryWorkerLeaseAdapter()
    lease = adapter.acquire(
        worker_id="w:1", budget_ref="budget:1", utc_clock=_fixed_clock,
    )
    assert lease is None


def test_acquire_returns_lease_with_correct_worker_id() -> None:
    adapter = InMemoryWorkerLeaseAdapter()
    adapter.enqueue(["work:1"])
    lease = adapter.acquire(
        worker_id="w:42", budget_ref="budget:1", utc_clock=_fixed_clock,
    )
    assert lease is not None
    assert lease.worker_id == "w:42"
    assert lease.work_item_ref == "work:1"


def test_acquire_respects_budget_gate_refusal() -> None:
    adapter = InMemoryWorkerLeaseAdapter(budget_gate=lambda _ref: False)
    adapter.enqueue(["work:1"])
    lease = adapter.acquire(
        worker_id="w:1", budget_ref="budget:1", utc_clock=_fixed_clock,
    )
    assert lease is None


def test_renew_extends_expires_at() -> None:
    adapter = InMemoryWorkerLeaseAdapter(lease_ttl=timedelta(seconds=30))
    adapter.enqueue(["work:1"])
    lease = adapter.acquire(
        worker_id="w:1", budget_ref="budget:1", utc_clock=_fixed_clock,
    )
    assert lease is not None
    renewed = adapter.renew(lease)
    assert renewed.expires_at == lease.expires_at + timedelta(seconds=30)


def test_release_success_aimd_window_increases() -> None:
    adapter = InMemoryWorkerLeaseAdapter(initial_window=1, max_window=8)
    adapter.enqueue(["work:1"])
    lease = adapter.acquire(
        worker_id="w:1", budget_ref="budget:1", utc_clock=_fixed_clock,
    )
    assert lease is not None
    adapter.release(lease, WorkOutcome(success=True))
    assert adapter.aimd_window_for("w:1") == 2


def test_release_failure_aimd_window_multiplicative_decrease() -> None:
    adapter = InMemoryWorkerLeaseAdapter(initial_window=1, max_window=8)
    adapter.enqueue(["work:1", "work:2", "work:3", "work:4"])
    # Walk the window up to 4.
    for i in range(3):
        lease = adapter.acquire(
            worker_id="w:1", budget_ref="budget:1", utc_clock=_fixed_clock,
        )
        assert lease is not None
        adapter.release(lease, WorkOutcome(success=True))
        del i
    assert adapter.aimd_window_for("w:1") == 4
    # Now fail → multiplicative decrease (floor div by 2).
    lease = adapter.acquire(
        worker_id="w:1", budget_ref="budget:1", utc_clock=_fixed_clock,
    )
    assert lease is not None
    adapter.release(
        lease, WorkOutcome(success=False, error_kind="transient"),
    )
    assert adapter.aimd_window_for("w:1") == 2


def test_acquire_lease_id_is_deterministic_for_same_inputs() -> None:
    adapter_a = InMemoryWorkerLeaseAdapter()
    adapter_a.enqueue(["work:1"])
    lease_a = adapter_a.acquire(
        worker_id="w:1", budget_ref="budget:1", utc_clock=_fixed_clock,
    )
    adapter_b = InMemoryWorkerLeaseAdapter()
    adapter_b.enqueue(["work:1"])
    lease_b = adapter_b.acquire(
        worker_id="w:1", budget_ref="budget:1", utc_clock=_fixed_clock,
    )
    assert lease_a is not None
    assert lease_b is not None
    assert lease_a.id == lease_b.id


def test_acquire_consumes_one_work_item_per_call() -> None:
    adapter = InMemoryWorkerLeaseAdapter()
    adapter.enqueue(["work:1", "work:2"])
    lease_a = adapter.acquire(
        worker_id="w:1", budget_ref="budget:1", utc_clock=_fixed_clock,
    )
    lease_b = adapter.acquire(
        worker_id="w:1", budget_ref="budget:1", utc_clock=_fixed_clock,
    )
    assert lease_a is not None
    assert lease_b is not None
    assert lease_a.work_item_ref == "work:1"
    assert lease_b.work_item_ref == "work:2"
