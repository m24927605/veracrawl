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


def append_runtime_event(
    store: InMemoryEventStore,
    *,
    run_id: str,
    objective_id: str,
    plan_id: str,
    event_type: str,
    payload_ref: Ref,
    causation_id: str,
    correlation_id: str,
    output_refs: list[Ref] | None = None,
    policy_decision_refs: list[Ref] | None = None,
    state_before: dict[str, object] | None = None,
    state_after: dict[str, object] | None = None,
    error: dict[str, object] | None = None,
    actor: str = "system",
) -> Ref:
    sequence = len(store.stream(run_id)) + 1
    event = CrawlRunEvent(
        id=f"event:{run_id}:{sequence}",
        run_id=run_id,
        objective_id=objective_id,
        crawl_plan_id=plan_id,
        sequence=sequence,
        event_type=event_type,
        event_type_spec_id=f"event-type:{event_type}",
        payload_ref=payload_ref,
        actor=actor,
        output_refs=output_refs or [],
        causation_id=causation_id,
        correlation_id=correlation_id,
        trace_id=f"trace:{run_id}:{sequence}",
        state_before=state_before,
        state_after=state_after,
        policy_decision_refs=policy_decision_refs or [],
        idempotency_key=f"idem:event:{run_id}:{sequence}",
        error=error or {},
    )
    return store.append(event)
