"""``InMemoryWorkerLeaseAdapter`` — single-process ``WorkerLeasePort`` (s16).

Pulls work items from an in-process FIFO queue, issues leases with a
tunable TTL, and tracks an AIMD success-rate state machine that the
caller's release outcome drives:

* ``release(WorkOutcome(success=True))`` → additive increase of the
  per-worker concurrency window (capped).
* ``release(WorkOutcome(success=False))`` → multiplicative decrease.

Replay invariant: lease IDs are
``stable_hash(worker_id + work_item_ref + acquired_at.isoformat())``
so two runs with the same inputs produce byte-equal IDs.

See ``docs/plans/general-purpose-crawler-agentification/
s16-worker-lease-port.md``.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.worker_lease import WorkerLease, WorkOutcome
from veracrawl.ports.worker_lease import BudgetGate

_AIMD_REF_PREFIX = "aimd-state:in-memory-worker-lease:"


class InMemoryWorkerLeaseAdapter:
    def __init__(
        self,
        *,
        lease_ttl: timedelta = timedelta(seconds=60),
        budget_gate: BudgetGate | None = None,
        initial_window: int = 1,
        max_window: int = 16,
    ) -> None:
        self._lease_ttl = lease_ttl
        self._budget_gate = budget_gate
        self._initial_window = initial_window
        self._max_window = max_window
        self._queue: deque[Ref] = deque()
        self._aimd_window: dict[str, int] = {}

    def enqueue(self, work_items: Iterable[Ref]) -> None:
        for ref in work_items:
            self._queue.append(ref)

    def acquire(
        self,
        *,
        worker_id: str,
        budget_ref: Ref,
        utc_clock: Callable[[], datetime],
    ) -> WorkerLease | None:
        if not self._queue:
            return None
        if self._budget_gate is not None and not self._budget_gate(budget_ref):
            return None
        work_item_ref = self._queue.popleft()
        acquired_at = utc_clock()
        expires_at = acquired_at + self._lease_ttl
        digest = stable_hash(
            f"{worker_id}|{work_item_ref}|{acquired_at.isoformat()}",
        )
        lease_id = f"lease:{worker_id}:{digest}"
        window = self._aimd_window.setdefault(worker_id, self._initial_window)
        return WorkerLease(
            id=lease_id,
            lease_ref=lease_id,
            work_item_ref=work_item_ref,
            worker_id=worker_id,
            acquired_at=acquired_at,
            expires_at=expires_at,
            aimd_state_ref=f"{_AIMD_REF_PREFIX}{worker_id}:window={window}",
            budget_ref=budget_ref,
        )

    def renew(self, lease: WorkerLease) -> WorkerLease:
        new_expires_at = lease.expires_at + self._lease_ttl
        return lease.model_copy(update={"expires_at": new_expires_at})

    def release(self, lease: WorkerLease, outcome: WorkOutcome) -> None:
        current = self._aimd_window.get(lease.worker_id, self._initial_window)
        if outcome.success:
            self._aimd_window[lease.worker_id] = min(
                self._max_window, current + 1,
            )
        else:
            self._aimd_window[lease.worker_id] = max(
                self._initial_window, current // 2,
            )

    def aimd_window_for(self, worker_id: str) -> int:
        return self._aimd_window.get(worker_id, self._initial_window)


__all__ = ["InMemoryWorkerLeaseAdapter"]
