"""``PlannerObservationFeedback`` contract (s5 of general-purpose-crawler-agentification).

Typed read projection of an s4 ``GraphObservationSnapshot`` for
planner consumption. The contract carries only derived adjacency
data; the snapshot itself is consumed by
``derive_planner_observation_feedback`` and is NOT stored as a
public field — see plan §Scope and the iter-3/iter-4 reservations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from pydantic import model_validator

from veracrawl.contracts.common import Ref, VeraModel

if TYPE_CHECKING:
    from veracrawl.contracts.graph_observation import GraphObservationSnapshot


def _is_http(v: str) -> bool:
    p = urlparse(v)
    return p.scheme in {"http", "https"} and bool(p.netloc)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


class PlannerObservationFeedback(VeraModel):
    id: str
    run_ref: Ref
    redirect_neighbours: list[str]
    canonical_targets: list[str]
    page_neighbour_count_by_url: dict[str, int]

    @model_validator(mode="after")
    def _validate(self) -> PlannerObservationFeedback:
        _require(bool(self.id.strip()), "id must be non-blank")
        _require(bool(self.run_ref.strip()), "run_ref must be non-blank")
        for i, u in enumerate(self.redirect_neighbours):
            _require(_is_http(u), f"redirect_neighbours[{i}] must be absolute http(s)")
        if len(set(self.redirect_neighbours)) != len(self.redirect_neighbours):
            raise ValueError("redirect_neighbours must not contain duplicates")
        for i, u in enumerate(self.canonical_targets):
            _require(_is_http(u), f"canonical_targets[{i}] must be absolute http(s)")
        if len(set(self.canonical_targets)) != len(self.canonical_targets):
            raise ValueError("canonical_targets must not contain duplicates")
        for u, c in self.page_neighbour_count_by_url.items():
            _require(_is_http(u), f"page_neighbour_count_by_url key {u!r} must be absolute http(s)")
            _require(c >= 0, f"page_neighbour_count_by_url[{u!r}] must be non-negative")
        return self


def derive_planner_observation_feedback(
    *, id: str, run_ref: Ref, snapshot: GraphObservationSnapshot,
) -> PlannerObservationFeedback:
    if snapshot.run_ref != run_ref:
        raise ValueError(
            "derive_planner_observation_feedback: run_ref must match snapshot.run_ref",
        )
    redirect_neighbours: list[str] = []
    seen_redirects: set[str] = set()
    for ev in snapshot.redirect_observed_events:
        if ev.to_canonical_url not in seen_redirects:
            redirect_neighbours.append(ev.to_canonical_url)
            seen_redirects.add(ev.to_canonical_url)
    canonical_targets: list[str] = []
    seen_canon: set[str] = set()
    for ev in snapshot.canonical_observed_events:
        if ev.canonical_target_url not in seen_canon:
            canonical_targets.append(ev.canonical_target_url)
            seen_canon.add(ev.canonical_target_url)
    page_counts: dict[str, int] = {}
    for ev in snapshot.page_structure_observed_events:
        page_counts[ev.page_canonical_url] = ev.discovered_link_count
    return PlannerObservationFeedback(
        id=id,
        run_ref=run_ref,
        redirect_neighbours=redirect_neighbours,
        canonical_targets=canonical_targets,
        page_neighbour_count_by_url=page_counts,
    )
