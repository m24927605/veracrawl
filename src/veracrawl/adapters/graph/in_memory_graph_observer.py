"""``InMemoryGraphObserver`` — s4 in-memory fixture adapter.

See ``docs/plans/general-purpose-crawler-agentification/
s4-graph-observation-port-contract.md``. Append-only per-type
event lists keyed by a single ``run_ref``; ``snapshot(*, id,
snapshot_at)`` emits a typed ``GraphObservationSnapshot`` with
events embedded directly (not refs).
"""

from __future__ import annotations

from datetime import datetime

from veracrawl.contracts.graph_observation import (
    CanonicalObservedEvent,
    GraphObservationSnapshot,
    PageStructureObservedEvent,
    RedirectObservedEvent,
    UrlObservedEvent,
)


def _check_run(event_kind: str, observer_run_ref: str, event_run_ref: str) -> None:
    if event_run_ref != observer_run_ref:
        raise ValueError(
            f"{event_kind} run_ref {event_run_ref!r} does not match observer "
            f"run_ref {observer_run_ref!r}"
        )


class InMemoryGraphObserver:
    """In-memory ``GraphObservationPort`` impl bound to one run."""

    def __init__(self, *, run_ref: str) -> None:
        if not run_ref.strip():
            raise ValueError("run_ref must be non-blank")
        self._run_ref = run_ref
        self._urls: list[UrlObservedEvent] = []
        self._redirects: list[RedirectObservedEvent] = []
        self._canonicals: list[CanonicalObservedEvent] = []
        self._pages: list[PageStructureObservedEvent] = []

    def record_url_observed(self, event: UrlObservedEvent) -> None:
        _check_run("record_url_observed", self._run_ref, event.run_ref)
        self._urls.append(event)

    def record_redirect_observed(self, event: RedirectObservedEvent) -> None:
        _check_run("record_redirect_observed", self._run_ref, event.run_ref)
        self._redirects.append(event)

    def record_canonical_observed(self, event: CanonicalObservedEvent) -> None:
        _check_run("record_canonical_observed", self._run_ref, event.run_ref)
        self._canonicals.append(event)

    def record_page_structure_observed(
        self, event: PageStructureObservedEvent
    ) -> None:
        _check_run("record_page_structure_observed", self._run_ref, event.run_ref)
        self._pages.append(event)

    def snapshot(
        self, *, id: str, snapshot_at: datetime
    ) -> GraphObservationSnapshot:
        return GraphObservationSnapshot(
            id=id, run_ref=self._run_ref,
            url_observed_events=list(self._urls),
            redirect_observed_events=list(self._redirects),
            canonical_observed_events=list(self._canonicals),
            page_structure_observed_events=list(self._pages),
            snapshot_at=snapshot_at,
        )
