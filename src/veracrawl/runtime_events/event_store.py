"""In-memory append-only event store for foundation tests."""

from __future__ import annotations

from collections import defaultdict

from veracrawl.contracts.common import Ref
from veracrawl.contracts.errors import ReplayValidationError
from veracrawl.contracts.event import CrawlRunEvent


class InMemoryEventStore:
    def __init__(self) -> None:
        self._events: dict[str, list[CrawlRunEvent]] = defaultdict(list)

    def append(self, event: CrawlRunEvent) -> Ref:
        current = self._events[event.run_id]
        expected_sequence = len(current) + 1
        if event.sequence != expected_sequence:
            raise ReplayValidationError(
                f"event sequence gap for {event.run_id}: expected {expected_sequence}, "
                f"got {event.sequence}"
            )
        current.append(event)
        return event.id

    def stream(self, run_id: str) -> list[CrawlRunEvent]:
        return list(self._events.get(run_id, []))
