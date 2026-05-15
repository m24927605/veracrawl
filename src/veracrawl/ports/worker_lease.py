"""``WorkerLeasePort`` (s16).

Multi-process scale port for leased work consumption. The fixture
adapter is single-process in-memory; s17 ships a real pool.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol, runtime_checkable

from veracrawl.contracts.common import Ref
from veracrawl.contracts.worker_lease import WorkerLease, WorkOutcome

BudgetGate = Callable[[Ref], bool]
"""Predicate the lease port consults before issuing a new lease.

Receives the budget ref; returns ``True`` to admit, ``False`` to
refuse. Replay-stable when the caller's budget tracking is.
"""


@runtime_checkable
class WorkerLeasePort(Protocol):
    def acquire(
        self,
        *,
        worker_id: str,
        budget_ref: Ref,
        utc_clock: Callable[[], datetime],
    ) -> WorkerLease | None: ...

    def renew(self, lease: WorkerLease) -> WorkerLease: ...

    def release(self, lease: WorkerLease, outcome: WorkOutcome) -> None: ...


__all__ = ["BudgetGate", "WorkerLeasePort"]
