"""``GraphObservationPort`` — s4 of general-purpose-crawler-agentification.

See ``docs/plans/general-purpose-crawler-agentification/
s4-graph-observation-port-contract.md``. Adapters capture URL /
redirect / canonical / page-structure observations from the live
runner; the read-side ``snapshot()`` projection feeds future
planner-feedback (s5) and replay (s11) slices.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from veracrawl.contracts.graph_observation import (
    CanonicalObservedEvent,
    GraphObservationSnapshot,
    PageStructureObservedEvent,
    RedirectObservedEvent,
    UrlObservedEvent,
)


@runtime_checkable
class GraphObservationPort(Protocol):
    """Record observations and expose a typed snapshot."""

    def record_url_observed(self, event: UrlObservedEvent) -> None:
        ...

    def record_redirect_observed(self, event: RedirectObservedEvent) -> None:
        ...

    def record_canonical_observed(self, event: CanonicalObservedEvent) -> None:
        ...

    def record_page_structure_observed(
        self, event: PageStructureObservedEvent
    ) -> None:
        ...

    def snapshot(
        self, *, id: str, snapshot_at: datetime
    ) -> GraphObservationSnapshot:
        ...


__all__ = ["GraphObservationPort"]
