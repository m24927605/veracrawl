"""``MultiprocessWorkerPool`` — real OS-process worker pool (s17 close).

Closes carry-forward gap #4: spawns ``worker_count`` actual
``multiprocessing.Process`` instances via the ``spawn`` context (so
state from the parent test runner doesn't leak in, and the pool works
cross-platform). Each subprocess pulls work items off a shared
``multiprocessing.Queue``, runs the caller-supplied execute callable,
and reports outcomes back via a second queue. The parent drains the
outcome queue, updates lease/AIMD state, and writes one
``CrawlRunEvent`` per outcome to the outbox event store.

Trade-offs vs ``WorkerPool`` (synchronous variant):

* execute callable MUST be importable via ``module:qualname`` (no
  closures — they can't be pickled across spawned processes). The
  ctor takes ``execute_reference: str`` instead of a callable.
* Slower for small workloads (subprocess startup ~100ms each).
* Useful for embarrassingly-parallel CPU-bound work that the GIL
  would serialize in a single-process driver.

See ``docs/plans/general-purpose-crawler-agentification/
s17-multi-process-worker-pool.md`` and the closing notes in
``WorkerPool`` (synchronous backend).
"""

from __future__ import annotations

import multiprocessing
from collections.abc import Callable
from datetime import datetime
from typing import Any

from veracrawl.adapters.work_queue._multiprocess_worker import spawn_worker
from veracrawl.adapters.work_queue.worker_pool import _outbox_event
from veracrawl.contracts.common import Ref
from veracrawl.contracts.worker_lease import WorkerLease, WorkOutcome
from veracrawl.ports.stores import EventStorePort
from veracrawl.ports.worker_lease import WorkerLeasePort


class MultiprocessWorkerPool:
    def __init__(
        self,
        *,
        pool_id: str,
        worker_count: int,
        lease_port: WorkerLeasePort,
        outbox_event_store: EventStorePort,
        run_id: str,
        execute_reference: str,
        utc_clock: Callable[[], datetime],
        utc_clock_ref: Ref,
        budget_ref: Ref,
    ) -> None:
        if worker_count < 1:
            raise ValueError("worker_count must be ≥ 1")
        if not utc_clock_ref.strip():
            raise ValueError("utc_clock_ref must be non-blank")
        if ":" not in execute_reference:
            raise ValueError(
                "execute_reference must be 'module:qualname' (e.g., "
                "'my.module:my_function')",
            )
        self._pool_id = pool_id
        self._worker_count = worker_count
        self._lease_port = lease_port
        self._outbox = outbox_event_store
        self._run_id = run_id
        self._execute_reference = execute_reference
        self._utc_clock = utc_clock
        self._utc_clock_ref = utc_clock_ref
        self._budget_ref = budget_ref
        self._ctx = multiprocessing.get_context("spawn")

    def run(self) -> dict[str, Any]:
        # Phase 1: drain the lease port into a list so the parent can
        # feed the input queue. The lease port stays in the parent
        # process (subprocesses don't share its state).
        pending: list[WorkerLease] = []
        while True:
            worker_id = f"worker:{self._pool_id}:{len(pending) % self._worker_count}"
            lease = self._lease_port.acquire(
                worker_id=worker_id,
                budget_ref=self._budget_ref,
                utc_clock=self._utc_clock,
            )
            if lease is None:
                break
            pending.append(lease)

        if not pending:
            return {
                "pool_id": self._pool_id,
                "run_id": self._run_id,
                "processed_count": 0,
                "outbox_event_count": 0,
            }

        # Phase 2: spawn subprocesses + queues.
        input_q: multiprocessing.Queue[str | None] = self._ctx.Queue()
        output_q: multiprocessing.Queue[tuple[str, str, str]] = self._ctx.Queue()
        processes: list[multiprocessing.Process] = []
        for i in range(self._worker_count):
            p = spawn_worker(
                self._ctx,
                input_q=input_q,
                output_q=output_q,
                worker_id=f"worker:{self._pool_id}:{i}",
                execute_reference=self._execute_reference,
            )
            processes.append(p)

        # Phase 3: enqueue work + sentinels (one None per worker).
        for lease in pending:
            input_q.put(lease.work_item_ref)
        for _ in range(self._worker_count):
            input_q.put(None)

        # Phase 4: drain outcomes + release leases + write outbox events.
        leases_by_ref = {lease.work_item_ref: lease for lease in pending}
        sequence = 0
        for _ in range(len(pending)):
            worker_id, work_item_ref, outcome_json = output_q.get()
            outcome = WorkOutcome.model_validate_json(outcome_json)
            lease = leases_by_ref[work_item_ref]
            self._lease_port.release(lease, outcome)
            sequence += 1
            self._outbox.append(_outbox_event(
                run_id=self._run_id,
                sequence=sequence,
                worker_id=worker_id,
                lease=lease,
                outcome=outcome,
            ))

        # Phase 5: join workers.
        for p in processes:
            p.join(timeout=5.0)
            if p.is_alive():
                p.terminate()
                p.join(timeout=1.0)

        return {
            "pool_id": self._pool_id,
            "run_id": self._run_id,
            "processed_count": len(pending),
            "outbox_event_count": sequence,
        }


__all__ = ["MultiprocessWorkerPool"]
