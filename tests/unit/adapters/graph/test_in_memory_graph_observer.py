"""Unit tests for ``InMemoryGraphObserver`` (s4 tests 21-26)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from veracrawl.adapters.graph.in_memory_graph_observer import InMemoryGraphObserver
from veracrawl.contracts.enums import CanonicalSource
from veracrawl.contracts.graph_observation import (
    CanonicalObservedEvent,
    PageStructureObservedEvent,
    RedirectObservedEvent,
    UrlObservedEvent,
)
from veracrawl.ports.graph_observation import GraphObservationPort

_T0 = datetime(2026, 5, 14, 12, 0, tzinfo=UTC)
_RUN = "run:test:1"


def _url(i: int) -> UrlObservedEvent:
    return UrlObservedEvent(
        id=f"url-event:{i}", run_ref=_RUN,
        canonical_url=f"https://a.example/{i}",
        depth=0, parent_canonical_url=None, source_ref="seed", observed_at=_T0,
    )


def _redirect(i: int) -> RedirectObservedEvent:
    return RedirectObservedEvent(
        id=f"redirect-event:{i}", run_ref=_RUN,
        from_canonical_url=f"https://a.example/{i}",
        to_canonical_url=f"https://a.example/{i}-target",
        status_code=301, observed_at=_T0,
    )


def _canonical(i: int) -> CanonicalObservedEvent:
    return CanonicalObservedEvent(
        id=f"canonical-event:{i}", run_ref=_RUN,
        linked_canonical_url=f"https://a.example/{i}?utm=x",
        canonical_target_url=f"https://a.example/{i}",
        source_kind=CanonicalSource.LINK_REL_CANONICAL, observed_at=_T0,
    )


def _page(i: int) -> PageStructureObservedEvent:
    return PageStructureObservedEvent(
        id=f"page-event:{i}", run_ref=_RUN,
        page_canonical_url=f"https://a.example/{i}",
        discovered_link_count=0, discovered_canonical_urls=[], observed_at=_T0,
    )


# Test 21
def test_observer_records_url_observed_in_emission_order() -> None:
    obs = InMemoryGraphObserver(run_ref=_RUN)
    events = [_url(1), _url(2), _url(3)]
    for ev in events:
        obs.record_url_observed(ev)
    snap = obs.snapshot(id="snap:1", snapshot_at=_T0)
    assert [e.id for e in snap.url_observed_events] == [e.id for e in events]


# Test 22
def test_observer_records_redirect_observed() -> None:
    obs = InMemoryGraphObserver(run_ref=_RUN)
    events = [_redirect(1), _redirect(2)]
    for ev in events:
        obs.record_redirect_observed(ev)
    snap = obs.snapshot(id="snap:1", snapshot_at=_T0)
    assert [e.id for e in snap.redirect_observed_events] == [e.id for e in events]


# Test 23
def test_observer_records_canonical_observed() -> None:
    obs = InMemoryGraphObserver(run_ref=_RUN)
    events = [_canonical(1), _canonical(2)]
    for ev in events:
        obs.record_canonical_observed(ev)
    snap = obs.snapshot(id="snap:1", snapshot_at=_T0)
    assert [e.id for e in snap.canonical_observed_events] == [e.id for e in events]


# Test 24
def test_observer_records_page_structure_observed() -> None:
    obs = InMemoryGraphObserver(run_ref=_RUN)
    events = [_page(1), _page(2)]
    for ev in events:
        obs.record_page_structure_observed(ev)
    snap = obs.snapshot(id="snap:1", snapshot_at=_T0)
    assert [e.id for e in snap.page_structure_observed_events] == [e.id for e in events]


# Test 25
def test_observer_snapshot_id_is_deterministic_from_inputs() -> None:
    snaps = []
    for _ in range(2):
        obs = InMemoryGraphObserver(run_ref=_RUN)
        obs.record_url_observed(_url(1))
        obs.record_redirect_observed(_redirect(1))
        obs.record_canonical_observed(_canonical(1))
        obs.record_page_structure_observed(_page(1))
        snaps.append(obs.snapshot(id="snap:test:1", snapshot_at=_T0))
    assert snaps[0].canonical_json() == snaps[1].canonical_json()


# Test 25a — mismatched run_ref rejected by every record_* method
def test_observer_rejects_recording_event_with_mismatched_run_ref() -> None:
    obs = InMemoryGraphObserver(run_ref="run:a")
    mismatched_url = _url(1).model_copy(update={"run_ref": "run:b"})
    mismatched_redirect = _redirect(1).model_copy(update={"run_ref": "run:b"})
    mismatched_canonical = _canonical(1).model_copy(update={"run_ref": "run:b"})
    mismatched_page = _page(1).model_copy(update={"run_ref": "run:b"})
    with pytest.raises(ValueError, match="record_url_observed"):
        obs.record_url_observed(mismatched_url)
    with pytest.raises(ValueError, match="record_redirect_observed"):
        obs.record_redirect_observed(mismatched_redirect)
    with pytest.raises(ValueError, match="record_canonical_observed"):
        obs.record_canonical_observed(mismatched_canonical)
    with pytest.raises(ValueError, match="record_page_structure_observed"):
        obs.record_page_structure_observed(mismatched_page)


# Test 26
def test_observer_implements_graph_observation_port() -> None:
    assert isinstance(
        InMemoryGraphObserver(run_ref="run:test:1"), GraphObservationPort,
    )
