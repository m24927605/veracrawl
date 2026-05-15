"""Unit tests for ``PriorityCrawlFrontier`` (s3.1, tests 1-18b)."""

from __future__ import annotations

import pytest

from veracrawl.contracts.crawl_planner import FrontierPriorityHint
from veracrawl.contracts.enums import FrontierMatchKind
from veracrawl.external_crawl.frontier import SkipReason
from veracrawl.external_crawl.priority_frontier import (
    PriorityCrawlFrontier,
    compute_item_priority,
)


def _admit_all() -> dict[str, object]:
    # Empty allowed_domains rejects everything in ``classify_url``; list
    # every host referenced by tests in this module.
    return {
        "allowed_domains": frozenset({
            "a.example", "a.example.com", "other.example.com",
            "other.example.org", "other.example", "host", "example",
        }),
        "denied_domains": frozenset(),
        "max_depth": 10,
        "max_pages": 100,
    }


def _hint(
    *, kind: FrontierMatchKind, value: str, delta: float,
    rationale: str = "rationale:test:1",
) -> FrontierPriorityHint:
    return FrontierPriorityHint(
        match_kind=kind, match_value=value, priority_delta=delta,
        rationale_ref=rationale,
    )


def _frontier(**overrides: object) -> PriorityCrawlFrontier:
    kwargs = _admit_all()
    kwargs.update(overrides)
    return PriorityCrawlFrontier(**kwargs)  # type: ignore[arg-type]


# Test 1
def test_empty_frontier_returns_none_on_pop() -> None:
    assert _frontier().pop() is None


# Test 2
def test_fifo_when_no_hints_apply() -> None:
    f = _frontier()
    for u in ("https://a.example/1", "https://a.example/2", "https://a.example/3"):
        f.enqueue(u, depth=0)
    popped = [f.pop(), f.pop(), f.pop()]
    canonicals = [p.canonical_url for p in popped if p is not None]
    assert canonicals == [
        "https://a.example/1", "https://a.example/2", "https://a.example/3",
    ]


# Test 3
def test_url_prefix_hint_boosts_matching_urls_first() -> None:
    f = _frontier()
    f.add_hints([_hint(
        kind=FrontierMatchKind.URL_PREFIX,
        value="https://a.example/match/", delta=0.5,
    )])
    f.enqueue("https://a.example/other/1", depth=0)
    f.enqueue("https://a.example/match/1", depth=0)
    first = f.pop()
    assert first is not None
    assert first.canonical_url == "https://a.example/match/1"


# Test 4
def test_host_glob_hint_matches_via_fnmatch() -> None:
    f = _frontier()
    f.add_hints([_hint(
        kind=FrontierMatchKind.HOST_GLOB, value="*.example.com", delta=0.7,
    )])
    f.enqueue("https://other.example.org/x", depth=0)
    f.enqueue("https://a.example.com/x", depth=0)
    first = f.pop()
    assert first is not None
    assert first.canonical_url == "https://a.example.com/x"


# Test 5
def test_host_glob_strips_port_via_hostname() -> None:
    f = _frontier()
    f.add_hints([_hint(
        kind=FrontierMatchKind.HOST_GLOB, value="host", delta=0.9,
    )])
    # When port is the default (443 for https), canonicalization drops
    # it; pick a non-default port to keep the URL intact.
    f.enqueue("https://other.example/x", depth=0)
    f.enqueue("https://host:8443/x", depth=0)
    first = f.pop()
    assert first is not None
    assert first.canonical_url.startswith("https://host")


# Test 6
def test_content_type_prefix_hint_recorded_but_no_effect() -> None:
    f = _frontier()
    f.add_hints([_hint(
        kind=FrontierMatchKind.CONTENT_TYPE_PREFIX,
        value="text/html", delta=0.5,
    )])
    f.enqueue("https://a.example/1", depth=0)
    f.enqueue("https://a.example/2", depth=0)
    # No URL/host match possible — fall through to FIFO.
    canonicals = [f.pop().canonical_url, f.pop().canonical_url]  # type: ignore[union-attr]
    assert canonicals == ["https://a.example/1", "https://a.example/2"]


# Test 7
def test_multiple_hints_sum_deltas() -> None:
    f = _frontier()
    f.add_hints([
        _hint(kind=FrontierMatchKind.URL_PREFIX,
              value="https://a.example/", delta=0.3, rationale="r:1"),
        _hint(kind=FrontierMatchKind.HOST_GLOB,
              value="a.example", delta=0.3, rationale="r:2"),
    ])
    # Bare priority (depth 0): 1.0; both hints apply → 1.6.
    p = compute_item_priority(
        canonical_url="https://a.example/p",
        depth=0,
        hints=[
            _hint(kind=FrontierMatchKind.URL_PREFIX,
                  value="https://a.example/", delta=0.3, rationale="r:1"),
            _hint(kind=FrontierMatchKind.HOST_GLOB,
                  value="a.example", delta=0.3, rationale="r:2"),
        ],
    )
    assert p == pytest.approx(1.6, abs=1e-9)


# Test 8
def test_negative_priority_delta_lowers_priority() -> None:
    f = _frontier()
    f.add_hints([_hint(
        kind=FrontierMatchKind.URL_PREFIX,
        value="https://a.example/bad/", delta=-0.5,
    )])
    f.enqueue("https://a.example/bad/1", depth=0)
    f.enqueue("https://a.example/good/1", depth=0)
    first = f.pop()
    assert first is not None
    assert first.canonical_url == "https://a.example/good/1"


# Test 9
def test_stable_tie_break_uses_enqueue_order() -> None:
    f = _frontier()
    urls = [f"https://a.example/{i}" for i in range(3)]
    for u in urls:
        f.enqueue(u, depth=0)
    popped = [f.pop().canonical_url for _ in range(3)]  # type: ignore[union-attr]
    assert popped == urls


# Test 10
def test_compute_item_priority_pure_function() -> None:
    args = {
        "canonical_url": "https://a.example/x",
        "depth": 1,
        "hints": [_hint(
            kind=FrontierMatchKind.URL_PREFIX,
            value="https://a.example/", delta=0.5,
        )],
    }
    a = compute_item_priority(**args)  # type: ignore[arg-type]
    b = compute_item_priority(**args)  # type: ignore[arg-type]
    assert a == b


# Test 11
def test_compute_item_priority_clamp_to_2_0() -> None:
    hints = [
        _hint(kind=FrontierMatchKind.URL_PREFIX,
              value="https://a.example/", delta=0.7, rationale=f"r:{i}")
        for i in range(3)
    ]
    p = compute_item_priority(
        canonical_url="https://a.example/x", depth=0, hints=hints,
    )
    # 1.0 + 3*0.7 = 3.1 → clamped to 2.0.
    assert p == pytest.approx(2.0, abs=1e-9)


# Test 12
def test_compute_item_priority_clamp_to_neg_2_0() -> None:
    hints = [
        _hint(kind=FrontierMatchKind.URL_PREFIX,
              value="https://a.example/", delta=-1.0, rationale=f"r:{i}")
        for i in range(4)
    ]
    p = compute_item_priority(
        canonical_url="https://a.example/x", depth=0, hints=hints,
    )
    # 1.0 + 4*(-1.0) = -3.0 → clamped to -2.0.
    assert p == pytest.approx(-2.0, abs=1e-9)


# Test 13
def test_enqueue_admission_unchanged_from_fifo_frontier() -> None:
    f = PriorityCrawlFrontier(
        allowed_domains=frozenset(["a.example"]),
        denied_domains=frozenset(),
        max_depth=2, max_pages=10,
    )
    outcome = f.enqueue("https://nope.example/x", depth=0)
    assert outcome.admitted is False
    assert outcome.skip_reason == SkipReason.OUTSIDE_ALLOWED_DOMAIN

    outcome = f.enqueue("https://a.example/x", depth=99)
    assert outcome.skip_reason == SkipReason.DEPTH_EXCEEDED


# Test 14
def test_budget_exhausted_returns_none_independently_of_priority() -> None:
    f = PriorityCrawlFrontier(
        allowed_domains=frozenset({"a.example"}),
        denied_domains=frozenset(),
        max_depth=5, max_pages=1,
    )
    f.enqueue("https://a.example/1", depth=0)
    f.enqueue("https://a.example/2", depth=0)
    item = f.pop()
    assert item is not None
    f.mark_fetched(item.canonical_url)
    assert f.pop() is None
    assert f.budget_exhausted() is True


# Test 15
def test_mark_fetched_and_skip_behavior_unchanged_from_fifo() -> None:
    f = _frontier()
    f.enqueue("https://a.example/1", depth=0)
    f.mark_fetched("https://a.example/1")
    counters = f.counters()
    assert counters.fetched == 1


# Test 16
def test_counters_match_fifo_frontier_for_same_inputs() -> None:
    f = _frontier()
    f.enqueue("https://a.example/1", depth=0)
    f.enqueue("https://a.example/2", depth=0)
    f.enqueue("https://a.example/1", depth=0)  # duplicate
    counters = f.counters()
    assert counters.enqueued == 2
    assert counters.skipped_by_reason[SkipReason.DUPLICATE] == 1


# Test 17
def test_events_emitted_in_pop_order() -> None:
    f = _frontier()
    f.add_hints([_hint(
        kind=FrontierMatchKind.URL_PREFIX,
        value="https://a.example/match/", delta=0.5,
    )])
    f.enqueue("https://a.example/other", depth=0)
    f.enqueue("https://a.example/match/x", depth=0)
    f.pop()
    f.pop()
    dequeue_events = [e for e in f.events() if e.kind == "dequeued"]
    canonical_pop_order = [e.canonical_url for e in dequeue_events]
    assert canonical_pop_order == [
        "https://a.example/match/x", "https://a.example/other",
    ]


# Test 18
def test_canonicalization_normalizes_url_before_priority_match() -> None:
    f = _frontier()
    f.add_hints([_hint(
        kind=FrontierMatchKind.URL_PREFIX,
        value="https://a.example/x", delta=0.5,
    )])
    f.enqueue("https://a.example/other", depth=0)
    f.enqueue("https://a.example/x?utm=y#frag", depth=0)
    first = f.pop()
    assert first is not None
    # Fragment stripped by canonicalize_url; matching still applies.
    assert first.canonical_url.startswith("https://a.example/x")
    assert "#frag" not in first.canonical_url


# Test 18a
def test_add_hints_reprioritizes_queued_items() -> None:
    f = _frontier()
    f.enqueue("https://a.example/1", depth=0)
    f.enqueue("https://a.example/2", depth=0)
    f.enqueue("https://a.example/3", depth=0)
    # No hints yet → FIFO baseline.
    f.add_hints([_hint(
        kind=FrontierMatchKind.URL_PREFIX,
        value="https://a.example/2", delta=0.9,
    )])
    first = f.pop()
    assert first is not None
    assert first.canonical_url == "https://a.example/2"


# Test 18b
def test_add_hints_accumulates_across_calls() -> None:
    f = _frontier()
    f.enqueue("https://a.example/1", depth=0)
    f.enqueue("https://a.example/2", depth=0)
    f.add_hints([_hint(
        kind=FrontierMatchKind.URL_PREFIX,
        value="https://a.example/1", delta=0.2,
    )])
    f.add_hints([_hint(
        kind=FrontierMatchKind.URL_PREFIX,
        value="https://a.example/2", delta=0.9,
    )])
    # Both hints active; URL #2's larger delta wins.
    first = f.pop()
    assert first is not None
    assert first.canonical_url == "https://a.example/2"
