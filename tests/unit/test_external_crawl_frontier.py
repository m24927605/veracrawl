"""Unit tests for ``ExternalCrawlFrontier``.

The frontier is a pure in-memory scheduler:
* admits / rejects URLs against the job spec's domain + scheme +
  private-network rules (via ``classify_url``);
* enforces ``max_depth`` and ``max_pages``;
* deduplicates by canonical URL;
* exposes every state transition as an event so the run report can
  reconstruct lineage.
"""

from __future__ import annotations

from veracrawl.external_crawl.frontier import (
    ExternalCrawlFrontier,
    FrontierItem,
    SkipReason,
)


def _frontier(
    *,
    max_depth: int = 2,
    max_pages: int = 10,
    allowed: set[str] | None = None,
    denied: set[str] | None = None,
    allow_loopback: bool = False,
) -> ExternalCrawlFrontier:
    return ExternalCrawlFrontier(
        allowed_domains=frozenset(allowed or {"example.com"}),
        denied_domains=frozenset(denied or set()),
        max_depth=max_depth,
        max_pages=max_pages,
        allow_loopback=allow_loopback,
    )


def test_enqueue_pop_round_trip() -> None:
    f = _frontier()
    outcome = f.enqueue("https://example.com/", depth=0)
    assert outcome.admitted
    assert outcome.canonical_url == "https://example.com/"

    item = f.pop()
    assert item is not None
    assert item.canonical_url == "https://example.com/"
    assert item.depth == 0


def test_pop_returns_none_when_empty() -> None:
    f = _frontier()
    assert f.pop() is None


def test_duplicate_url_skipped() -> None:
    f = _frontier()
    f.enqueue("https://example.com/", depth=0)
    second = f.enqueue("https://example.com/", depth=0)
    assert second.admitted is False
    assert second.skip_reason == SkipReason.DUPLICATE


def test_canonical_dedup_detects_case_and_default_port() -> None:
    f = _frontier()
    f.enqueue("https://example.com/page", depth=0)
    dup = f.enqueue("HTTPS://Example.com:443/page", depth=0)
    assert dup.admitted is False
    assert dup.skip_reason == SkipReason.DUPLICATE


def test_outside_allowed_domain_skipped() -> None:
    f = _frontier()
    outcome = f.enqueue("https://other.test/", depth=0)
    assert outcome.admitted is False
    assert outcome.skip_reason == SkipReason.OUTSIDE_ALLOWED_DOMAIN


def test_denied_domain_skipped() -> None:
    f = _frontier(denied={"shop.example.com"})
    outcome = f.enqueue("https://shop.example.com/", depth=0)
    assert outcome.admitted is False
    assert outcome.skip_reason == SkipReason.DENIED_DOMAIN


def test_unsupported_scheme_skipped() -> None:
    f = _frontier()
    outcome = f.enqueue("ftp://example.com/file", depth=0)
    assert outcome.admitted is False
    assert outcome.skip_reason == SkipReason.UNSUPPORTED_SCHEME


def test_private_network_denied_unless_loopback_opt_in() -> None:
    f_blocking = _frontier(allowed={"127.0.0.1"}, allow_loopback=False)
    out_blocked = f_blocking.enqueue("http://127.0.0.1/", depth=0)
    assert out_blocked.skip_reason == SkipReason.PRIVATE_NETWORK_DENIED

    f_allow = _frontier(allowed={"127.0.0.1"}, allow_loopback=True)
    out_allow = f_allow.enqueue("http://127.0.0.1/", depth=0)
    assert out_allow.admitted


def test_depth_exceeded_skipped() -> None:
    f = _frontier(max_depth=1)
    assert f.enqueue("https://example.com/a", depth=1).admitted
    outcome = f.enqueue("https://example.com/b", depth=2)
    assert outcome.admitted is False
    assert outcome.skip_reason == SkipReason.DEPTH_EXCEEDED


def test_max_pages_budget_enforced_on_pop() -> None:
    # ``max_pages`` caps successful fetches (mark_fetched calls), not
    # admissions; the scheduler keeps admitting until pop() refuses
    # because the budget is exhausted.
    f = _frontier(max_pages=2)
    f.enqueue("https://example.com/a", depth=0)
    f.enqueue("https://example.com/b", depth=0)
    f.enqueue("https://example.com/c", depth=0)

    a = f.pop()
    assert a is not None
    f.mark_fetched(a.canonical_url)
    b = f.pop()
    assert b is not None
    f.mark_fetched(b.canonical_url)
    assert f.pop() is None
    assert f.budget_exhausted()


def test_robots_denied_recorded_via_skip() -> None:
    # Robots checks need network I/O so they happen outside the
    # frontier. The caller pops a URL, fails the robots check, and
    # reports it back via skip() so the run report records the
    # denial uniformly with the in-frontier skips.
    f = _frontier()
    f.enqueue("https://example.com/a", depth=0)
    item = f.pop()
    assert item is not None
    f.skip(item.canonical_url, SkipReason.ROBOTS_DENIED)
    counters = f.counters()
    assert counters.skipped_by_reason[SkipReason.ROBOTS_DENIED] == 1


def test_events_record_every_transition() -> None:
    f = _frontier()
    f.enqueue("https://example.com/a", depth=0)
    f.enqueue("https://other.test/", depth=0)
    item = f.pop()
    assert item is not None
    f.mark_fetched(item.canonical_url)

    kinds = [event.kind for event in f.events()]
    assert "enqueued" in kinds
    assert "skipped" in kinds
    assert "dequeued" in kinds
    assert "fetched" in kinds


def test_counters_reflect_outcomes() -> None:
    f = _frontier(max_pages=5)
    f.enqueue("https://example.com/a", depth=0)
    f.enqueue("https://example.com/b", depth=0)
    f.enqueue("https://other.test/", depth=0)
    item = f.pop()
    assert item is not None
    f.mark_fetched(item.canonical_url)

    counters = f.counters()
    assert counters.enqueued == 2
    assert counters.fetched == 1
    assert counters.skipped_by_reason[SkipReason.OUTSIDE_ALLOWED_DOMAIN] == 1


def test_frontier_item_carries_parent_lineage() -> None:
    f = _frontier()
    f.enqueue("https://example.com/", depth=0, parent_canonical_url=None)
    f.enqueue(
        "https://example.com/page",
        depth=1,
        parent_canonical_url="https://example.com/",
    )

    seen: list[FrontierItem] = []
    while (item := f.pop()) is not None:
        seen.append(item)
    assert seen[0].parent_canonical_url is None
    assert seen[1].parent_canonical_url == "https://example.com/"
