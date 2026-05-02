"""Durable event cursor helpers."""

from __future__ import annotations

from veracrawl.contracts.durable import EventCursorRecord
from veracrawl.contracts.event import CrawlRunEvent


def event_sequence_gaps(events: list[CrawlRunEvent]) -> list[int]:
    if not events:
        return []
    sequences = sorted(event.sequence for event in events)
    expected = set(range(sequences[0], sequences[-1] + 1))
    return sorted(expected.difference(sequences))


def build_event_cursor_record(run_ref: str, events: list[CrawlRunEvent]) -> EventCursorRecord:
    if not events:
        return EventCursorRecord(
            id=f"event-cursor:{run_ref}:empty",
            run_ref=run_ref,
            from_sequence=1,
            to_sequence=1,
            event_refs=["event:none"],
            contiguous=True,
        )
    ordered = sorted(events, key=lambda event: event.sequence)
    gaps = event_sequence_gaps(ordered)
    return EventCursorRecord(
        id=f"event-cursor:{run_ref}:{ordered[0].sequence}-{ordered[-1].sequence}",
        run_ref=run_ref,
        from_sequence=ordered[0].sequence,
        to_sequence=ordered[-1].sequence,
        event_refs=[event.id for event in ordered],
        contiguous=not gaps,
        missing_sequence_numbers=gaps,
    )
