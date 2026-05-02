"""Scheduler frontier and lease ports."""

from __future__ import annotations

from typing import Protocol

from veracrawl.contracts.common import Ref
from veracrawl.contracts.scheduler import FrontierItem, QueueLease


class SchedulerStatePort(Protocol):
    def save_frontier_item(self, item: FrontierItem) -> Ref: ...

    def get_frontier_item(self, item_ref: Ref) -> FrontierItem | None: ...

    def list_frontier_items(self, run_ref: Ref | None = None) -> list[FrontierItem]: ...

    def save_queue_lease(self, lease: QueueLease) -> Ref: ...

    def get_queue_lease(self, lease_ref: Ref) -> QueueLease | None: ...

    def list_queue_leases(self, run_ref: Ref | None = None) -> list[QueueLease]: ...
