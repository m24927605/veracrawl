"""``WorkerPool`` — synchronous multi-worker driver (s17).

Drives N logical workers through the s16 ``WorkerLeasePort``. Each
"worker" acquires a lease, runs the caller-supplied work callable,
and releases the lease with the resulting ``WorkOutcome``. AIMD
state evolves through the lease port; outbox event-stream is the
authoritative ordering.

Per s17 plan iter-5 reservation R1: the work callable is the
``execute_work`` closure passed to the ctor. It receives the
acquired ``WorkerLease`` and returns a ``WorkOutcome``. Workers
are not actually spawned as OS processes in this slice (synchronous
backend); the multi-process backend is deferred to a follow-up
slice with the same ``WorkerPool`` API.

Per R2, every clock read goes through the injected ``utc_clock``;
worker ids are deterministic (``worker:{pool_id}:{i}``).

See ``docs/plans/general-purpose-crawler-agentification/
s17-multi-process-worker-pool.md``.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from veracrawl.contracts.common import Ref
from veracrawl.contracts.event import CrawlRunEvent
from veracrawl.contracts.worker_lease import WorkerLease, WorkOutcome
from veracrawl.ports.stores import EventStorePort
from veracrawl.ports.worker_lease import WorkerLeasePort


def _outbox_event(
    *, run_id: str, sequence: int, worker_id: str, lease: WorkerLease,
    outcome: WorkOutcome,
) -> CrawlRunEvent:
    return CrawlRunEvent(
        id=f"event:{run_id}:{sequence}",
        run_id=run_id,
        objective_id="objective:worker-pool",
        crawl_plan_id="plan:worker-pool",
        sequence=sequence,
        event_type=(
            "work_item_succeeded" if outcome.success else "work_item_failed"
        ),
        event_type_spec_id="event-type:work_item",
        payload_ref=lease.work_item_ref,
        actor=worker_id,
        causation_id=lease.id,
        correlation_id=lease.lease_ref,
        trace_id=f"trace:{run_id}:{sequence}",
        idempotency_key=f"idem:{lease.id}",
    )


class WorkerPool:
    def __init__(
        self,
        *,
        pool_id: str,
        worker_count: int,
        lease_port: WorkerLeasePort,
        outbox_event_store: EventStorePort,
        run_id: str,
        execute_work: Callable[[WorkerLease], WorkOutcome],
        utc_clock: Callable[[], datetime],
        utc_clock_ref: Ref,
        budget_ref: Ref,
    ) -> None:
        if worker_count < 1:
            raise ValueError("worker_count must be ≥ 1")
        if not utc_clock_ref.strip():
            raise ValueError("utc_clock_ref must be non-blank")
        self._pool_id = pool_id
        self._worker_count = worker_count
        self._lease_port = lease_port
        self._outbox = outbox_event_store
        self._run_id = run_id
        self._execute_work = execute_work
        self._utc_clock = utc_clock
        self._utc_clock_ref = utc_clock_ref
        self._budget_ref = budget_ref
        self._processed_count = 0
        self._processed_lease_ids: set[str] = set()

    def run(self) -> dict[str, Any]:
        """Drive workers until the lease port returns None for all of them.

        Returns a small dict report so callers can inspect the
        outcome without spelunking the outbox.
        """

        sequence = 0
        round_idx = 0
        while True:
            any_acquired = False
            for worker_idx in range(self._worker_count):
                worker_id = f"worker:{self._pool_id}:{worker_idx}"
                lease = self._lease_port.acquire(
                    worker_id=worker_id,
                    budget_ref=self._budget_ref,
                    utc_clock=self._utc_clock,
                )
                if lease is None:
                    continue
                any_acquired = True
                if lease.id in self._processed_lease_ids:
                    # Defensive: dedup if the port handed the same
                    # lease twice for any reason.
                    continue
                self._processed_lease_ids.add(lease.id)
                outcome = self._execute_work(lease)
                self._lease_port.release(lease, outcome)
                sequence += 1
                self._outbox.append(_outbox_event(
                    run_id=self._run_id,
                    sequence=sequence,
                    worker_id=worker_id,
                    lease=lease,
                    outcome=outcome,
                ))
                self._processed_count += 1
            round_idx += 1
            if not any_acquired:
                break
        return {
            "pool_id": self._pool_id,
            "run_id": self._run_id,
            "processed_count": self._processed_count,
            "rounds": round_idx,
            "outbox_event_count": sequence,
        }


__all__ = ["WorkerPool"]
