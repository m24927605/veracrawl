"""Contract tests for s4 graph-observation events."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CanonicalSource
from veracrawl.contracts.graph_observation import (
    CanonicalObservedEvent,
    GraphObservationSnapshot,
    PageStructureObservedEvent,
    RedirectObservedEvent,
    UrlObservedEvent,
)

_T0 = datetime(2026, 5, 14, 12, 0, tzinfo=UTC)


def _url_payload() -> dict[str, Any]:
    return {
        "id": "url-event:1", "run_ref": "run:test:1",
        "canonical_url": "https://a.example/p",
        "depth": 0, "parent_canonical_url": None,
        "source_ref": "seed", "observed_at": _T0,
    }


def _redirect_payload() -> dict[str, Any]:
    return {
        "id": "redirect-event:1", "run_ref": "run:test:1",
        "from_canonical_url": "https://a.example/p",
        "to_canonical_url": "https://a.example/q",
        "status_code": 301, "observed_at": _T0,
    }


def _canonical_payload() -> dict[str, Any]:
    return {
        "id": "canonical-event:1", "run_ref": "run:test:1",
        "linked_canonical_url": "https://a.example/p?utm=x",
        "canonical_target_url": "https://a.example/p",
        "source_kind": CanonicalSource.LINK_REL_CANONICAL,
        "observed_at": _T0,
    }


def _page_payload() -> dict[str, Any]:
    return {
        "id": "page-event:1", "run_ref": "run:test:1",
        "page_canonical_url": "https://a.example/p",
        "discovered_link_count": 2,
        "discovered_canonical_urls": ["https://a.example/q", "https://a.example/r"],
        "observed_at": _T0,
    }


def _snapshot_payload() -> dict[str, Any]:
    return {
        "id": "snapshot:1", "run_ref": "run:test:1",
        "url_observed_events": [], "redirect_observed_events": [],
        "canonical_observed_events": [], "page_structure_observed_events": [],
        "snapshot_at": _T0,
    }


# Test 1
def test_url_observed_event_rejects_non_http_canonical_url() -> None:
    with pytest.raises(ValidationError, match="canonical_url"):
        UrlObservedEvent(**(_url_payload() | {"canonical_url": "file:///tmp"}))


# Test 2
def test_url_observed_event_rejects_negative_depth() -> None:
    with pytest.raises(ValidationError, match="depth"):
        UrlObservedEvent(**(_url_payload() | {"depth": -1}))


# Test 3
def test_url_observed_event_accepts_none_parent() -> None:
    UrlObservedEvent(**(_url_payload() | {"parent_canonical_url": None}))


# Test 4
def test_url_observed_event_rejects_non_http_parent() -> None:
    with pytest.raises(ValidationError, match="parent_canonical_url"):
        UrlObservedEvent(**(_url_payload() | {"parent_canonical_url": "not-a-url"}))


# Test 5
def test_url_observed_event_rejects_blank_source_ref() -> None:
    with pytest.raises(ValidationError, match="source_ref"):
        UrlObservedEvent(**(_url_payload() | {"source_ref": ""}))


# Test 6
def test_redirect_observed_event_rejects_self_redirect() -> None:
    with pytest.raises(ValidationError, match="from"):
        RedirectObservedEvent(**(_redirect_payload() | {
            "to_canonical_url": "https://a.example/p",
        }))


# Test 7
def test_redirect_observed_event_rejects_status_out_of_range() -> None:
    with pytest.raises(ValidationError, match="status_code"):
        RedirectObservedEvent(**(_redirect_payload() | {"status_code": 200}))


# Test 8
def test_redirect_observed_event_rejects_non_http_to_url() -> None:
    with pytest.raises(ValidationError, match="to_canonical_url"):
        RedirectObservedEvent(**(_redirect_payload() | {"to_canonical_url": "file:///x"}))


# Test 8a
def test_redirect_observed_event_rejects_non_http_from_url() -> None:
    with pytest.raises(ValidationError, match="from_canonical_url"):
        RedirectObservedEvent(**(_redirect_payload() | {"from_canonical_url": "file:///x"}))


# Test 9
def test_canonical_observed_event_rejects_self_canonical() -> None:
    with pytest.raises(ValidationError, match="linked"):
        CanonicalObservedEvent(**(_canonical_payload() | {
            "canonical_target_url": "https://a.example/p?utm=x",
        }))


# Test 10
def test_canonical_observed_event_rejects_non_http_linked_url() -> None:
    with pytest.raises(ValidationError, match="linked_canonical_url"):
        CanonicalObservedEvent(**(_canonical_payload() | {"linked_canonical_url": "x"}))


# Test 10a
def test_canonical_observed_event_rejects_non_http_target_url() -> None:
    with pytest.raises(ValidationError, match="canonical_target_url"):
        CanonicalObservedEvent(**(_canonical_payload() | {"canonical_target_url": "x"}))


# Test 11
def test_page_structure_observed_event_rejects_negative_link_count() -> None:
    with pytest.raises(ValidationError, match="discovered_link_count"):
        PageStructureObservedEvent(**(_page_payload() | {"discovered_link_count": -1}))


# Test 11a
def test_page_structure_observed_event_rejects_non_http_page_url() -> None:
    with pytest.raises(ValidationError, match="page_canonical_url"):
        PageStructureObservedEvent(**(_page_payload() | {"page_canonical_url": "x"}))


# Test 12
def test_page_structure_observed_event_rejects_duplicate_canonical_urls() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        PageStructureObservedEvent(**(_page_payload() | {
            "discovered_canonical_urls": ["https://a.example/q", "https://a.example/q"],
        }))


# Test 13
def test_page_structure_observed_event_rejects_non_http_in_discovered_list() -> None:
    with pytest.raises(ValidationError, match="discovered_canonical_urls"):
        PageStructureObservedEvent(**(_page_payload() | {
            "discovered_canonical_urls": ["https://a.example/q", "file:///bad"],
        }))


# Test 14
def test_graph_observation_snapshot_allows_empty_ref_lists() -> None:
    GraphObservationSnapshot(**_snapshot_payload())


# Test 15
def test_graph_observation_snapshot_rejects_blank_run_ref() -> None:
    with pytest.raises(ValidationError, match="run_ref"):
        GraphObservationSnapshot(**(_snapshot_payload() | {"run_ref": ""}))


# Tests 15a-15i — non-blank id/run_ref tests
def test_url_observed_event_rejects_blank_id() -> None:
    with pytest.raises(ValidationError, match="id"):
        UrlObservedEvent(**(_url_payload() | {"id": ""}))


def test_url_observed_event_rejects_blank_run_ref() -> None:
    with pytest.raises(ValidationError, match="run_ref"):
        UrlObservedEvent(**(_url_payload() | {"run_ref": ""}))


def test_redirect_observed_event_rejects_blank_id() -> None:
    with pytest.raises(ValidationError, match="id"):
        RedirectObservedEvent(**(_redirect_payload() | {"id": ""}))


def test_redirect_observed_event_rejects_blank_run_ref() -> None:
    with pytest.raises(ValidationError, match="run_ref"):
        RedirectObservedEvent(**(_redirect_payload() | {"run_ref": ""}))


def test_canonical_observed_event_rejects_blank_id() -> None:
    with pytest.raises(ValidationError, match="id"):
        CanonicalObservedEvent(**(_canonical_payload() | {"id": ""}))


def test_canonical_observed_event_rejects_blank_run_ref() -> None:
    with pytest.raises(ValidationError, match="run_ref"):
        CanonicalObservedEvent(**(_canonical_payload() | {"run_ref": ""}))


def test_page_structure_observed_event_rejects_blank_id() -> None:
    with pytest.raises(ValidationError, match="id"):
        PageStructureObservedEvent(**(_page_payload() | {"id": ""}))


def test_page_structure_observed_event_rejects_blank_run_ref() -> None:
    with pytest.raises(ValidationError, match="run_ref"):
        PageStructureObservedEvent(**(_page_payload() | {"run_ref": ""}))


def test_graph_observation_snapshot_rejects_blank_id() -> None:
    with pytest.raises(ValidationError, match="id"):
        GraphObservationSnapshot(**(_snapshot_payload() | {"id": ""}))


# Tests 15j-15n — naive datetime tests
_NAIVE = datetime(2026, 5, 14, 12, 0)  # noqa: DTZ001


def test_url_observed_event_rejects_naive_observed_at() -> None:
    with pytest.raises(ValidationError, match="observed_at"):
        UrlObservedEvent(**(_url_payload() | {"observed_at": _NAIVE}))


def test_redirect_observed_event_rejects_naive_observed_at() -> None:
    with pytest.raises(ValidationError, match="observed_at"):
        RedirectObservedEvent(**(_redirect_payload() | {"observed_at": _NAIVE}))


def test_canonical_observed_event_rejects_naive_observed_at() -> None:
    with pytest.raises(ValidationError, match="observed_at"):
        CanonicalObservedEvent(**(_canonical_payload() | {"observed_at": _NAIVE}))


def test_page_structure_observed_event_rejects_naive_observed_at() -> None:
    with pytest.raises(ValidationError, match="observed_at"):
        PageStructureObservedEvent(**(_page_payload() | {"observed_at": _NAIVE}))


def test_graph_observation_snapshot_rejects_naive_snapshot_at() -> None:
    with pytest.raises(ValidationError, match="snapshot_at"):
        GraphObservationSnapshot(**(_snapshot_payload() | {"snapshot_at": _NAIVE}))


# Tests 15o-15s — aware-non-UTC datetime tests
_NON_UTC = datetime(2026, 5, 14, 12, 0, tzinfo=timezone(timedelta(hours=8)))


def test_url_observed_event_rejects_non_utc_observed_at() -> None:
    with pytest.raises(ValidationError, match="observed_at"):
        UrlObservedEvent(**(_url_payload() | {"observed_at": _NON_UTC}))


def test_redirect_observed_event_rejects_non_utc_observed_at() -> None:
    with pytest.raises(ValidationError, match="observed_at"):
        RedirectObservedEvent(**(_redirect_payload() | {"observed_at": _NON_UTC}))


def test_canonical_observed_event_rejects_non_utc_observed_at() -> None:
    with pytest.raises(ValidationError, match="observed_at"):
        CanonicalObservedEvent(**(_canonical_payload() | {"observed_at": _NON_UTC}))


def test_page_structure_observed_event_rejects_non_utc_observed_at() -> None:
    with pytest.raises(ValidationError, match="observed_at"):
        PageStructureObservedEvent(**(_page_payload() | {"observed_at": _NON_UTC}))


def test_graph_observation_snapshot_rejects_non_utc_snapshot_at() -> None:
    with pytest.raises(ValidationError, match="snapshot_at"):
        GraphObservationSnapshot(**(_snapshot_payload() | {"snapshot_at": _NON_UTC}))


# Test 15t — event run_ref must match snapshot run_ref
def test_graph_observation_snapshot_rejects_event_with_mismatched_run_ref() -> None:
    mismatched_url = UrlObservedEvent(**(_url_payload() | {"run_ref": "run:other"}))
    with pytest.raises(ValidationError, match="run_ref"):
        GraphObservationSnapshot(**(_snapshot_payload() | {
            "url_observed_events": [mismatched_url],
        }))


# Tests 15u-15y — missing observed_at / snapshot_at
def test_url_observed_event_rejects_missing_observed_at() -> None:
    payload = _url_payload()
    del payload["observed_at"]
    with pytest.raises(ValidationError, match="observed_at"):
        UrlObservedEvent(**payload)


def test_redirect_observed_event_rejects_missing_observed_at() -> None:
    payload = _redirect_payload()
    del payload["observed_at"]
    with pytest.raises(ValidationError, match="observed_at"):
        RedirectObservedEvent(**payload)


def test_canonical_observed_event_rejects_missing_observed_at() -> None:
    payload = _canonical_payload()
    del payload["observed_at"]
    with pytest.raises(ValidationError, match="observed_at"):
        CanonicalObservedEvent(**payload)


def test_page_structure_observed_event_rejects_missing_observed_at() -> None:
    payload = _page_payload()
    del payload["observed_at"]
    with pytest.raises(ValidationError, match="observed_at"):
        PageStructureObservedEvent(**payload)


def test_graph_observation_snapshot_rejects_missing_snapshot_at() -> None:
    payload = _snapshot_payload()
    del payload["snapshot_at"]
    with pytest.raises(ValidationError, match="snapshot_at"):
        GraphObservationSnapshot(**payload)


# Tests 15z-15dd — missing id
def test_url_observed_event_rejects_missing_id() -> None:
    payload = _url_payload()
    del payload["id"]
    with pytest.raises(ValidationError, match="id"):
        UrlObservedEvent(**payload)


def test_redirect_observed_event_rejects_missing_id() -> None:
    payload = _redirect_payload()
    del payload["id"]
    with pytest.raises(ValidationError, match="id"):
        RedirectObservedEvent(**payload)


def test_canonical_observed_event_rejects_missing_id() -> None:
    payload = _canonical_payload()
    del payload["id"]
    with pytest.raises(ValidationError, match="id"):
        CanonicalObservedEvent(**payload)


def test_page_structure_observed_event_rejects_missing_id() -> None:
    payload = _page_payload()
    del payload["id"]
    with pytest.raises(ValidationError, match="id"):
        PageStructureObservedEvent(**payload)


def test_graph_observation_snapshot_rejects_missing_id() -> None:
    payload = _snapshot_payload()
    del payload["id"]
    with pytest.raises(ValidationError, match="id"):
        GraphObservationSnapshot(**payload)


# Tests 15ee-15ii — missing run_ref
def test_url_observed_event_rejects_missing_run_ref() -> None:
    payload = _url_payload()
    del payload["run_ref"]
    with pytest.raises(ValidationError, match="run_ref"):
        UrlObservedEvent(**payload)


def test_redirect_observed_event_rejects_missing_run_ref() -> None:
    payload = _redirect_payload()
    del payload["run_ref"]
    with pytest.raises(ValidationError, match="run_ref"):
        RedirectObservedEvent(**payload)


def test_canonical_observed_event_rejects_missing_run_ref() -> None:
    payload = _canonical_payload()
    del payload["run_ref"]
    with pytest.raises(ValidationError, match="run_ref"):
        CanonicalObservedEvent(**payload)


def test_page_structure_observed_event_rejects_missing_run_ref() -> None:
    payload = _page_payload()
    del payload["run_ref"]
    with pytest.raises(ValidationError, match="run_ref"):
        PageStructureObservedEvent(**payload)


def test_graph_observation_snapshot_rejects_missing_run_ref() -> None:
    payload = _snapshot_payload()
    del payload["run_ref"]
    with pytest.raises(ValidationError, match="run_ref"):
        GraphObservationSnapshot(**payload)


# Test 15jj — missing source_ref (UrlObservedEvent only)
def test_url_observed_event_rejects_missing_source_ref() -> None:
    payload = _url_payload()
    del payload["source_ref"]
    with pytest.raises(ValidationError, match="source_ref"):
        UrlObservedEvent(**payload)
