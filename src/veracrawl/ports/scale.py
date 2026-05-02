"""Scale infrastructure port abstractions."""

from __future__ import annotations

from typing import Protocol

from veracrawl.contracts.scale import QueueItem, ShardLease


class ScaleQueuePort(Protocol):
    """Infrastructure-neutral queue boundary."""

    def enqueue(self, item: QueueItem) -> QueueItem:
        """Record a queue item through the queue adapter."""

    def acquire_lease(self, item: QueueItem, worker_id: str) -> ShardLease:
        """Acquire a lease for a queue item."""

    def heartbeat(self, lease: ShardLease) -> ShardLease:
        """Refresh a lease heartbeat."""
