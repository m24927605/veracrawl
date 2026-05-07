"""Unit tests for ``UrllibRobotsParser`` (Phase 1 step 1.2 default).

The production default for ``RobotsPort`` parses ``robots.txt`` using
``urllib.robotparser.RobotFileParser`` and adds the four guarantees
the design.md §4 Phase 1 deliverables call out:

1. Fetch once per host per run (in-memory cache + per-host lock — a
   second concurrent ``evaluate`` for the same host must not re-issue
   the HTTP request).
2. TTL — cached entries expire after a configurable period and the
   next ``evaluate`` re-fetches.
3. Optional on-disk cache survives across processes (the design
   requires "TTL + on-disk cache").
4. Single source-of-truth user-agent — the user-agent passed to
   ``evaluate`` is also used to fetch ``robots.txt`` so a UA-specific
   ``robots.txt`` cannot serve permissive rules to one UA while we
   crawl with another.

The tests inject a fake fetcher; no real network is touched. ``crawl_delay``
and ``request_rate`` are exercised against real ``robots.txt`` strings
to keep the parsing path under direct test (urllib's behavior is the
source of truth — we wrap it, we don't re-implement it).
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from veracrawl.adapters.network.urllib_robots import (
    RobotsFetchResult,
    UrllibRobotsParser,
    make_httpx_robots_fetcher,
)
from veracrawl.ports.robots import RobotsPort

_DEFAULT_UA = "VeraCrawlTest/1.0"


def _ua_specific_robots() -> str:
    # urllib.robotparser splits the caller-supplied UA on ``/`` (so
    # ``"VeraCrawlTest/1.0"`` matches ``User-agent: VeraCrawlTest``) and
    # does substring containment, which is why the directive name omits
    # the version. This is urllib's contract — we wrap it, we don't
    # second-guess the matcher.
    return (
        "User-agent: *\n"
        "Disallow: /admin\n"
        "Crawl-delay: 2\n"
        "Request-rate: 1/5\n"
        "\n"
        "User-agent: VeraCrawlTest\n"
        "Disallow: /private\n"
        "Allow: /\n"
    )


def _allow_all_robots() -> str:
    return "User-agent: *\nAllow: /\n"


def _disallow_all_robots() -> str:
    return "User-agent: *\nDisallow: /\n"


def _make_fetcher(
    body: str,
    status: int = 200,
    counter: list[tuple[str, str]] | None = None,
) -> Callable[[str, str], RobotsFetchResult]:
    def _fetch(robots_url: str, user_agent: str) -> RobotsFetchResult:
        if counter is not None:
            counter.append((robots_url, user_agent))
        return RobotsFetchResult(status=status, body=body)

    return _fetch


def test_parser_satisfies_robots_port_protocol() -> None:
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_allow_all_robots()))
    assert isinstance(parser, RobotsPort)


def test_evaluate_returns_allow_for_permissive_robots() -> None:
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_allow_all_robots()))
    advice = parser.evaluate("https://example.test/path", user_agent=_DEFAULT_UA)
    assert advice.is_allowed is True


def test_evaluate_returns_deny_for_blocking_robots() -> None:
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_disallow_all_robots()))
    advice = parser.evaluate("https://example.test/anything", user_agent=_DEFAULT_UA)
    assert advice.is_allowed is False


def test_evaluate_parses_crawl_delay() -> None:
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_ua_specific_robots()))
    advice = parser.evaluate("https://example.test/p", user_agent="OtherBot/1.0")
    assert advice.crawl_delay == 2.0


def test_evaluate_parses_request_rate() -> None:
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_ua_specific_robots()))
    advice = parser.evaluate("https://example.test/p", user_agent="OtherBot/1.0")
    assert advice.request_rate == (1, 5)


def test_evaluate_uses_ua_specific_rules() -> None:
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_ua_specific_robots()))
    # Wildcard group blocks /admin; UA-specific group blocks /private but
    # allows everything else.
    advice = parser.evaluate("https://example.test/private", user_agent=_DEFAULT_UA)
    assert advice.is_allowed is False


def test_evaluate_treats_404_as_allow_all() -> None:
    parser = UrllibRobotsParser(fetcher=_make_fetcher("", status=404))
    advice = parser.evaluate("https://example.test/", user_agent=_DEFAULT_UA)
    # IETF guidance: a 404 robots.txt means no rules — fully permissive.
    assert advice.is_allowed is True


def test_evaluate_treats_5xx_as_disallow_all() -> None:
    parser = UrllibRobotsParser(fetcher=_make_fetcher("", status=503))
    advice = parser.evaluate("https://example.test/", user_agent=_DEFAULT_UA)
    # A 5xx must NOT be silently treated as allow-all — the spec says
    # the crawler should assume disallow until robots.txt can be
    # fetched cleanly. Cooperative crawlers fail closed.
    assert advice.is_allowed is False


def test_fetch_once_per_host() -> None:
    counter: list[tuple[str, str]] = []
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_allow_all_robots(), counter=counter))
    parser.evaluate("https://example.test/a", user_agent=_DEFAULT_UA)
    parser.evaluate("https://example.test/b", user_agent=_DEFAULT_UA)
    parser.evaluate("https://example.test/c", user_agent=_DEFAULT_UA)
    assert len(counter) == 1


def test_fetch_per_distinct_host() -> None:
    counter: list[tuple[str, str]] = []
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_allow_all_robots(), counter=counter))
    parser.evaluate("https://a.example.test/", user_agent=_DEFAULT_UA)
    parser.evaluate("https://b.example.test/", user_agent=_DEFAULT_UA)
    assert len(counter) == 2


def test_fetch_uses_caller_user_agent() -> None:
    """The robots fetcher must receive the same UA the evaluator uses."""

    counter: list[tuple[str, str]] = []
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_allow_all_robots(), counter=counter))
    parser.evaluate("https://example.test/", user_agent=_DEFAULT_UA)
    assert counter == [("https://example.test/robots.txt", _DEFAULT_UA)]


def test_ttl_expires_and_refetches() -> None:
    counter: list[tuple[str, str]] = []
    clock = [1000.0]
    parser = UrllibRobotsParser(
        fetcher=_make_fetcher(_allow_all_robots(), counter=counter),
        ttl_seconds=60.0,
        clock_fn=lambda: clock[0],
    )
    parser.evaluate("https://example.test/a", user_agent=_DEFAULT_UA)
    clock[0] = 1100.0  # 100s elapsed -> past TTL
    parser.evaluate("https://example.test/b", user_agent=_DEFAULT_UA)
    assert len(counter) == 2


def test_ttl_within_window_does_not_refetch() -> None:
    counter: list[tuple[str, str]] = []
    clock = [1000.0]
    parser = UrllibRobotsParser(
        fetcher=_make_fetcher(_allow_all_robots(), counter=counter),
        ttl_seconds=60.0,
        clock_fn=lambda: clock[0],
    )
    parser.evaluate("https://example.test/", user_agent=_DEFAULT_UA)
    clock[0] = 1030.0
    parser.evaluate("https://example.test/x", user_agent=_DEFAULT_UA)
    assert len(counter) == 1


def test_fetch_robots_url_is_origin_rooted() -> None:
    counter: list[tuple[str, str]] = []
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_allow_all_robots(), counter=counter))
    parser.evaluate("https://shop.example.test/p/123?x=1", user_agent=_DEFAULT_UA)
    assert counter[0][0] == "https://shop.example.test/robots.txt"


def test_concurrent_fetch_is_collapsed_to_one(tmp_path: Path) -> None:
    """Two threads asking for the same host concurrently fetch once."""

    counter: list[tuple[str, str]] = []
    fetch_started = threading.Event()
    release_fetch = threading.Event()

    def slow_fetcher(robots_url: str, user_agent: str) -> RobotsFetchResult:
        counter.append((robots_url, user_agent))
        fetch_started.set()
        release_fetch.wait(timeout=2.0)
        return RobotsFetchResult(status=200, body=_allow_all_robots())

    parser = UrllibRobotsParser(fetcher=slow_fetcher)

    def worker() -> None:
        parser.evaluate("https://example.test/", user_agent=_DEFAULT_UA)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    fetch_started.wait(timeout=2.0)
    t2.start()
    release_fetch.set()
    t1.join(timeout=2.0)
    t2.join(timeout=2.0)
    assert not t1.is_alive() and not t2.is_alive()
    assert len(counter) == 1


def test_on_disk_cache_persists_across_parser_instances(tmp_path: Path) -> None:
    counter: list[tuple[str, str]] = []
    fetcher = _make_fetcher(_allow_all_robots(), counter=counter)
    monotonic_clock = [1000.0]
    wallclock = [1_700_000_000.0]

    parser_a = UrllibRobotsParser(
        fetcher=fetcher,
        cache_dir=tmp_path,
        ttl_seconds=60.0,
        clock_fn=lambda: monotonic_clock[0],
        wallclock_fn=lambda: wallclock[0],
    )
    parser_a.evaluate("https://example.test/", user_agent=_DEFAULT_UA)
    assert len(counter) == 1

    # New process / new parser instance — fetcher should NOT be hit
    # because the on-disk entry is fresh. We advance both clocks by
    # the same amount so the wall-clock TTL on disk is still valid.
    parser_b = UrllibRobotsParser(
        fetcher=fetcher,
        cache_dir=tmp_path,
        ttl_seconds=60.0,
        clock_fn=lambda: monotonic_clock[0] + 30.0,
        wallclock_fn=lambda: wallclock[0] + 30.0,
    )
    parser_b.evaluate("https://example.test/", user_agent=_DEFAULT_UA)
    assert len(counter) == 1


def test_on_disk_cache_re_fetch_after_ttl(tmp_path: Path) -> None:
    counter: list[tuple[str, str]] = []
    fetcher = _make_fetcher(_allow_all_robots(), counter=counter)
    monotonic_clock = [1000.0]
    wallclock = [1_700_000_000.0]

    parser_a = UrllibRobotsParser(
        fetcher=fetcher,
        cache_dir=tmp_path,
        ttl_seconds=60.0,
        clock_fn=lambda: monotonic_clock[0],
        wallclock_fn=lambda: wallclock[0],
    )
    parser_a.evaluate("https://example.test/", user_agent=_DEFAULT_UA)

    # Past TTL on the wall clock — disk cache must not satisfy the read.
    parser_b = UrllibRobotsParser(
        fetcher=fetcher,
        cache_dir=tmp_path,
        ttl_seconds=60.0,
        clock_fn=lambda: monotonic_clock[0] + 200.0,
        wallclock_fn=lambda: wallclock[0] + 200.0,
    )
    parser_b.evaluate("https://example.test/", user_agent=_DEFAULT_UA)
    assert len(counter) == 2


def test_fetch_failure_treated_as_disallow() -> None:
    """A transport-level fetcher failure is fail-closed (cooperative crawler)."""

    def failing_fetcher(robots_url: str, user_agent: str) -> RobotsFetchResult:
        raise RuntimeError("network down")

    parser = UrllibRobotsParser(fetcher=failing_fetcher)
    advice = parser.evaluate("https://example.test/p", user_agent=_DEFAULT_UA)
    assert advice.is_allowed is False


# -- codex iter-1 regression tests --------------------------------


def test_distinct_user_agents_get_distinct_cached_rules() -> None:
    """Origins can serve UA-specific robots.txt — the cache must not mix.

    Codex iter-1 important: keying the cache only on host meant a
    first evaluation populated the cache and a second evaluation with
    a different UA reused the wrong rules.
    """

    bodies = {
        "VeraCrawlA/1": "User-agent: *\nDisallow: /a\n",
        "VeraCrawlB/1": "User-agent: *\nDisallow: /b\n",
    }

    def per_ua_fetcher(robots_url: str, user_agent: str) -> RobotsFetchResult:
        ua_key = user_agent.split("/")[0] + "/1"
        return RobotsFetchResult(status=200, body=bodies[ua_key])

    parser = UrllibRobotsParser(fetcher=per_ua_fetcher)
    # UA A gets blocked on /a but not /b.
    advice_a_on_a = parser.evaluate("https://example.test/a", user_agent="VeraCrawlA/1")
    advice_a_on_b = parser.evaluate("https://example.test/b", user_agent="VeraCrawlA/1")
    # UA B sees the opposite rule set.
    advice_b_on_a = parser.evaluate("https://example.test/a", user_agent="VeraCrawlB/1")
    advice_b_on_b = parser.evaluate("https://example.test/b", user_agent="VeraCrawlB/1")
    assert advice_a_on_a.is_allowed is False
    assert advice_a_on_b.is_allowed is True
    assert advice_b_on_a.is_allowed is True
    assert advice_b_on_b.is_allowed is False


def test_distinct_user_agents_each_trigger_a_fetch() -> None:
    """Each distinct UA on the same host triggers its own robots.txt fetch.

    Without this, a second UA would reuse the first UA's parser and
    the per-UA rule set would be silently wrong (codex iter-1 important).
    """

    counter: list[tuple[str, str]] = []
    parser = UrllibRobotsParser(fetcher=_make_fetcher(_allow_all_robots(), counter=counter))
    parser.evaluate("https://example.test/", user_agent="VeraCrawlA/1")
    parser.evaluate("https://example.test/", user_agent="VeraCrawlB/1")
    assert len(counter) == 2
    # Each fetch carried its own UA — the fetcher saw both.
    assert {ua for _, ua in counter} == {"VeraCrawlA/1", "VeraCrawlB/1"}


# -- codex iter-2 regression tests --------------------------------


def test_failed_fetch_is_cached_for_short_ttl() -> None:
    """Transport failures cache a fail-closed marker for a short TTL.

    Codex iter-2 important: returning ``None`` without caching meant
    every URL on a host triggered a fresh failing fetch during an
    outage, breaking the fetch-once-per-host guarantee.
    """

    counter = [0]

    def failing_fetcher(robots_url: str, user_agent: str) -> RobotsFetchResult:
        counter[0] += 1
        raise RuntimeError("transport down")

    monotonic_clock = [1000.0]
    parser = UrllibRobotsParser(
        fetcher=failing_fetcher,
        ttl_seconds=3600.0,
        failure_ttl_seconds=60.0,
        clock_fn=lambda: monotonic_clock[0],
        wallclock_fn=lambda: 1_700_000_000.0 + (monotonic_clock[0] - 1000.0),
    )
    # Three evaluations during the outage → one fetch attempt.
    parser.evaluate("https://example.test/a", user_agent=_DEFAULT_UA)
    parser.evaluate("https://example.test/b", user_agent=_DEFAULT_UA)
    parser.evaluate("https://example.test/c", user_agent=_DEFAULT_UA)
    assert counter[0] == 1


def test_failure_cache_expires_after_failure_ttl_and_retries() -> None:
    counter = [0]

    def flapping_fetcher(robots_url: str, user_agent: str) -> RobotsFetchResult:
        counter[0] += 1
        raise RuntimeError("transport down")

    monotonic_clock = [1000.0]
    parser = UrllibRobotsParser(
        fetcher=flapping_fetcher,
        ttl_seconds=3600.0,
        failure_ttl_seconds=60.0,
        clock_fn=lambda: monotonic_clock[0],
    )
    parser.evaluate("https://example.test/a", user_agent=_DEFAULT_UA)
    monotonic_clock[0] = 1100.0  # past failure_ttl
    parser.evaluate("https://example.test/b", user_agent=_DEFAULT_UA)
    assert counter[0] == 2


def test_disk_cache_metadata_uses_wallclock_not_monotonic(tmp_path: Path) -> None:
    """On-disk metadata uses wall-clock time so it survives process restarts.

    Codex iter-2 important: monotonic time is process-relative, so a
    persisted ``monotonic()`` timestamp is meaningless to the next
    process. Reading the meta file should be a wall-clock value.
    """

    counter: list[tuple[str, str]] = []
    fetcher = _make_fetcher(_allow_all_robots(), counter=counter)

    parser = UrllibRobotsParser(
        fetcher=fetcher,
        cache_dir=tmp_path,
        ttl_seconds=3600.0,
        clock_fn=lambda: 1000.0,  # monotonic — small number
        wallclock_fn=lambda: 1_700_000_000.0,  # wall clock — epoch-scale
    )
    parser.evaluate("https://example.test/", user_agent=_DEFAULT_UA)

    meta_files = list(tmp_path.glob("*.meta.json"))
    assert len(meta_files) == 1
    import json as _json  # local import — keep test surface obvious

    meta = _json.loads(meta_files[0].read_text(encoding="utf-8"))
    assert "fetched_at_wallclock" in meta
    assert meta["fetched_at_wallclock"] >= 1_000_000_000.0
    # Crucially: no leftover monotonic field on disk.
    assert "fetched_at" not in meta or meta.get("fetched_at") is None


def test_make_httpx_robots_fetcher_returns_callable_with_correct_signature() -> None:
    """The production helper returns a fetcher with the documented shape.

    Codex iter-2 critical: production callers must use a low-level
    fetcher that does not consult ``RobotsPort``; this helper exists
    so the recursion isn't possible by construction.
    """

    fetcher = make_httpx_robots_fetcher(timeout_s=5.0)
    # Callable with the (robots_url, user_agent) -> RobotsFetchResult shape.
    import inspect

    sig = inspect.signature(fetcher)
    params = list(sig.parameters)
    assert len(params) == 2


def test_disk_cache_preserves_original_body_verbatim(tmp_path: Path) -> None:
    """On-disk cache stores the original fetched body, not a parser rendering.

    Codex iter-1 important: ``str(RobotFileParser)`` is a parser-state
    rendering and is not a faithful round-trip — comments and unknown
    directives can be dropped. The cache layer must keep the bytes we
    actually received.
    """

    body_with_comments = (
        "# top-of-file comment we want to preserve\n"
        "User-agent: *\n"
        "Disallow: /admin\n"
        "Allow: /public\n"
        "# trailing comment\n"
        "Sitemap: https://example.test/sitemap.xml\n"
    )

    parser_a = UrllibRobotsParser(
        fetcher=_make_fetcher(body_with_comments),
        cache_dir=tmp_path,
    )
    parser_a.evaluate("https://example.test/", user_agent=_DEFAULT_UA)

    # Find the body file written to disk and assert byte-exact content.
    body_files = list(tmp_path.glob("*.robots.txt"))
    assert len(body_files) == 1
    on_disk = body_files[0].read_text(encoding="utf-8")
    assert on_disk == body_with_comments
