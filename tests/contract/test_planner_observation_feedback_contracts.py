"""Contract tests for ``PlannerObservationFeedback`` (s5 tests 1-17).

See ``docs/plans/general-purpose-crawler-agentification/
s5-planner-observation-feedback.md`` — the typed read projection
of a graph snapshot consumed by ``DeterministicCrawlPlannerV2``.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CanonicalSource
from veracrawl.contracts.graph_observation import (
    CanonicalObservedEvent,
    GraphObservationSnapshot,
    PageStructureObservedEvent,
    RedirectObservedEvent,
)
from veracrawl.contracts.planner_observation_feedback import (
    PlannerObservationFeedback,
    derive_planner_observation_feedback,
)

_T = datetime(2026, 5, 14, 12, 0, tzinfo=UTC)
_RUN = "run:s5:1"


def _empty_snapshot(run_ref: str = _RUN) -> GraphObservationSnapshot:
    return GraphObservationSnapshot(
        id="snap:test:1",
        run_ref=run_ref,
        url_observed_events=[],
        redirect_observed_events=[],
        canonical_observed_events=[],
        page_structure_observed_events=[],
        snapshot_at=_T,
    )


def _redirect(i: int, target: str, run_ref: str = _RUN) -> RedirectObservedEvent:
    return RedirectObservedEvent(
        id=f"redir:{i}",
        run_ref=run_ref,
        from_canonical_url=f"https://src.example/{i}",
        to_canonical_url=target,
        status_code=301,
        observed_at=_T,
    )


def _canonical(i: int, target: str, run_ref: str = _RUN) -> CanonicalObservedEvent:
    return CanonicalObservedEvent(
        id=f"canon:{i}",
        run_ref=run_ref,
        linked_canonical_url=f"https://linked.example/{i}",
        canonical_target_url=target,
        source_kind=CanonicalSource.LINK_REL_CANONICAL,
        observed_at=_T,
    )


def _page(i: int, url: str, count: int, run_ref: str = _RUN) -> PageStructureObservedEvent:
    return PageStructureObservedEvent(
        id=f"page:{i}",
        run_ref=run_ref,
        page_canonical_url=url,
        discovered_link_count=count,
        discovered_canonical_urls=[],
        observed_at=_T,
    )


def _fb(**overrides: object) -> PlannerObservationFeedback:
    base = {
        "id": "fb:test:1",
        "run_ref": _RUN,
        "redirect_neighbours": [],
        "canonical_targets": [],
        "page_neighbour_count_by_url": {},
    }
    base.update(overrides)
    return PlannerObservationFeedback(**base)  # type: ignore[arg-type]


# Test 1
def test_feedback_rejects_blank_id() -> None:
    with pytest.raises(ValidationError, match="id"):
        _fb(id="")


# Test 2
def test_feedback_rejects_blank_run_ref() -> None:
    with pytest.raises(ValidationError, match="run_ref"):
        _fb(run_ref="")


# Test 3
def test_feedback_rejects_non_http_redirect_neighbour() -> None:
    with pytest.raises(ValidationError, match="redirect_neighbours"):
        _fb(redirect_neighbours=["ftp://x.example/a"])


# Test 4
def test_feedback_rejects_duplicate_redirect_neighbour() -> None:
    with pytest.raises(ValidationError, match="redirect_neighbours"):
        _fb(redirect_neighbours=["https://x.example/a", "https://x.example/a"])


# Test 5
def test_feedback_rejects_non_http_canonical_target() -> None:
    with pytest.raises(ValidationError, match="canonical_targets"):
        _fb(canonical_targets=["mailto:a@example"])


# Test 6
def test_feedback_rejects_duplicate_canonical_target() -> None:
    with pytest.raises(ValidationError, match="canonical_targets"):
        _fb(canonical_targets=["https://x.example/a", "https://x.example/a"])


# Test 7
def test_feedback_rejects_non_http_page_neighbour_url() -> None:
    with pytest.raises(ValidationError, match="page_neighbour_count_by_url"):
        _fb(page_neighbour_count_by_url={"file:///x": 5})


# Test 8
def test_feedback_rejects_negative_page_neighbour_count() -> None:
    with pytest.raises(ValidationError, match="page_neighbour_count_by_url"):
        _fb(page_neighbour_count_by_url={"https://x.example/a": -1})


# Test 9
def test_feedback_accepts_minimal_empty_collections() -> None:
    fb = _fb()
    assert fb.redirect_neighbours == []
    assert fb.canonical_targets == []
    assert fb.page_neighbour_count_by_url == {}


# Test 10
def test_feedback_has_no_snapshot_field() -> None:
    assert "snapshot" not in PlannerObservationFeedback.model_fields


# Test 10a
def test_feedback_model_fields_exactly() -> None:
    assert set(PlannerObservationFeedback.model_fields.keys()) == {
        "id",
        "run_ref",
        "redirect_neighbours",
        "canonical_targets",
        "page_neighbour_count_by_url",
    }


# Test 11
def test_derive_extracts_redirect_neighbours_in_order() -> None:
    snap = _empty_snapshot().model_copy(
        update={
            "redirect_observed_events": [
                _redirect(1, "https://a.example/x"),
                _redirect(2, "https://b.example/y"),
                _redirect(3, "https://c.example/z"),
            ],
        },
    )
    fb = derive_planner_observation_feedback(id="fb:1", run_ref=_RUN, snapshot=snap)
    assert fb.redirect_neighbours == [
        "https://a.example/x",
        "https://b.example/y",
        "https://c.example/z",
    ]


# Test 12
def test_derive_dedups_redirect_neighbours() -> None:
    snap = _empty_snapshot().model_copy(
        update={
            "redirect_observed_events": [
                _redirect(1, "https://a.example/x"),
                _redirect(2, "https://a.example/x"),
            ],
        },
    )
    fb = derive_planner_observation_feedback(id="fb:1", run_ref=_RUN, snapshot=snap)
    assert fb.redirect_neighbours == ["https://a.example/x"]


# Test 13
def test_derive_extracts_canonical_targets_in_order() -> None:
    snap = _empty_snapshot().model_copy(
        update={
            "canonical_observed_events": [
                _canonical(1, "https://a.example/x"),
                _canonical(2, "https://b.example/y"),
            ],
        },
    )
    fb = derive_planner_observation_feedback(id="fb:1", run_ref=_RUN, snapshot=snap)
    assert fb.canonical_targets == ["https://a.example/x", "https://b.example/y"]


# Test 14
def test_derive_dedups_canonical_targets() -> None:
    snap = _empty_snapshot().model_copy(
        update={
            "canonical_observed_events": [
                _canonical(1, "https://a.example/x"),
                _canonical(2, "https://a.example/x"),
            ],
        },
    )
    fb = derive_planner_observation_feedback(id="fb:1", run_ref=_RUN, snapshot=snap)
    assert fb.canonical_targets == ["https://a.example/x"]


# Test 15
def test_derive_extracts_page_neighbour_counts() -> None:
    snap = _empty_snapshot().model_copy(
        update={
            "page_structure_observed_events": [
                _page(1, "https://hub.example/", 3),
                _page(2, "https://hub.example/", 7),
            ],
        },
    )
    fb = derive_planner_observation_feedback(id="fb:1", run_ref=_RUN, snapshot=snap)
    assert fb.page_neighbour_count_by_url == {"https://hub.example/": 7}


# Test 16
def test_derive_is_deterministic_for_identical_input() -> None:
    snap = _empty_snapshot().model_copy(
        update={
            "redirect_observed_events": [_redirect(1, "https://a.example/x")],
            "canonical_observed_events": [_canonical(1, "https://b.example/y")],
            "page_structure_observed_events": [_page(1, "https://c.example/", 5)],
        },
    )
    fb1 = derive_planner_observation_feedback(id="fb:1", run_ref=_RUN, snapshot=snap)
    fb2 = derive_planner_observation_feedback(id="fb:1", run_ref=_RUN, snapshot=snap)
    assert fb1.canonical_json() == fb2.canonical_json()


# Test 17
def test_derive_rejects_run_ref_mismatch_with_snapshot() -> None:
    snap = _empty_snapshot(run_ref="run:other")
    with pytest.raises(ValueError, match="run_ref must match snapshot.run_ref"):
        derive_planner_observation_feedback(id="fb:1", run_ref=_RUN, snapshot=snap)
