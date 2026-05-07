"""``UrllibRobotsParser`` — production default for ``RobotsPort``.

Wraps ``urllib.robotparser.RobotFileParser`` with the four guarantees
the design.md §4 Phase 1 deliverables call out:

1. **Fetch once per host per run.** An in-memory per-host cache plus a
   per-host lock collapses concurrent ``evaluate`` calls into one
   network fetch — even under multi-threaded scheduling.
2. **TTL.** Cache entries expire after ``ttl_seconds`` so a long-running
   crawl does not pin a stale ``robots.txt``.
3. **Optional on-disk cache.** When ``cache_dir`` is configured, fetched
   ``robots.txt`` content + a metadata sidecar is persisted so a fresh
   process / parser instance reuses the entry until TTL expiry.
4. **Single source-of-truth user-agent.** The ``user_agent`` callers
   pass to ``evaluate`` is the same UA the fetcher receives — a UA-
   specific ``robots.txt`` cannot serve permissive rules to one UA
   while we crawl with another.

Failure semantics:

- HTTP **404** → allow-all (IETF guidance: "no rules" means
  unrestricted).
- HTTP **5xx** or any transport failure → fail closed: the URL is
  treated as disallowed for cooperative crawling. The charter
  (``docs/09:116`` §Safety Boundary) requires we honor robots; if we
  cannot determine the rules, we must not assume permission.

The parsing of ``Disallow`` / ``Allow`` / ``Crawl-delay`` /
``Request-rate`` directives is delegated to
``urllib.robotparser.RobotFileParser`` which is the de-facto reference
parser for Python crawlers. We don't re-implement it; we wrap it.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx

from veracrawl.ports.robots import RobotsAdvice
from veracrawl.runtime_support.logging import get_logger

_logger = get_logger(__name__)

_DEFAULT_TTL_SECONDS: Final[float] = 3600.0
# Short TTL for cached fetch failures (transport / 5xx). The design
# requires fetch-once-per-host, but ``None`` returned without caching
# meant every URL on a host triggered a fresh failing fetch during an
# outage (codex iter-2 important). We cache failures briefly so
# subsequent ``evaluate`` calls during the outage window short-circuit
# without re-issuing the request, but still recover automatically once
# the TTL elapses.
_DEFAULT_FAILURE_TTL_SECONDS: Final[float] = 60.0
_META_SUFFIX: Final[str] = ".meta.json"
_BODY_SUFFIX: Final[str] = ".robots.txt"
# Wall-clock failure marker for the on-disk cache: status code reserved
# for "fetcher could not produce a real HTTP status" (transport error,
# DNS failure, etc.). Persisted entries with this status are read back
# as fail-closed regardless of body.
_FETCH_FAILURE_STATUS: Final[int] = -1


@dataclass(frozen=True)
class RobotsFetchResult:
    """Carrier for a single ``robots.txt`` fetch outcome.

    ``status`` is the HTTP status code. ``body`` is the response body
    (text); for non-200 responses the body is irrelevant and may be
    empty.
    """

    status: int
    body: str


RobotsFetcher = Callable[[str, str], RobotsFetchResult]


@dataclass
class _CachedEntry:
    parser: RobotFileParser
    # Monotonic timestamp for in-memory TTL math. Monotonic time is
    # immune to wall-clock jumps but is process-relative, so it is
    # **not** persisted to disk (codex iter-2 important).
    fetched_at: float
    # Wall-clock (epoch) timestamp persisted to disk so a fresh process
    # / parser instance can compute TTL against its own clock without
    # relying on the previous process's monotonic origin.
    fetched_at_wallclock: float
    status: int
    # Track the robots URL alongside the parser. ``RobotFileParser`` does
    # carry an ``url`` attribute at runtime (set in ``__init__`` /
    # ``set_url``) but it isn't in the typeshed stubs, so we keep our
    # own copy to satisfy ``mypy --strict`` without ``# type: ignore``.
    robots_url: str
    # Original fetched body (codex iter-1 important): the on-disk cache
    # writes this verbatim instead of ``str(RobotFileParser)`` because
    # the latter is a parser-state rendering and may not faithfully
    # round-trip (e.g., comments / unknown directives are dropped).
    # ``None`` for synthesised parsers (404 → empty rules, 5xx →
    # disallow-all) where there is no original body to preserve.
    body: str | None


class UrllibRobotsParser:
    """``RobotsPort`` impl using ``urllib.robotparser.RobotFileParser``.

    Construction parameters:

    * ``fetcher``: callable that fetches ``robots.txt`` for a given
      ``robots_url`` using a given ``user_agent``. The fetcher must be
      a low-level HTTP client that **does not itself consult a
      ``RobotsPort``** — using ``StdlibHttpSourceAdapter`` here would
      cause infinite recursion (it now checks robots before every
      fetch, so fetching ``/robots.txt`` would require evaluating
      robots first). Use :func:`make_httpx_robots_fetcher` for
      production wiring; tests inject a callable directly.
    * ``ttl_seconds``: in-memory + on-disk cache TTL for successful
      fetches. Defaults to one hour, the same order of magnitude most
      well-behaved crawlers use.
    * ``failure_ttl_seconds``: in-memory + on-disk cache TTL for fetch
      failures (transport error / 5xx). Short by design (60s default)
      so an outage doesn't pin fail-closed for an hour, but long
      enough to avoid hammering an origin during a flap.
    * ``cache_dir``: optional directory for the on-disk cache. ``None``
      means "in-memory only" (still fetch-once-per-host per process).
    * ``clock_fn``: monotonic time for in-memory TTL math.
    * ``wallclock_fn``: epoch / wall-clock time for the persisted
      on-disk metadata. Monotonic time is process-relative and would
      be invalid across process restarts (codex iter-2 important).
    """

    def __init__(
        self,
        *,
        fetcher: RobotsFetcher,
        ttl_seconds: float = _DEFAULT_TTL_SECONDS,
        failure_ttl_seconds: float = _DEFAULT_FAILURE_TTL_SECONDS,
        cache_dir: Path | None = None,
        clock_fn: Callable[[], float] = time.monotonic,
        wallclock_fn: Callable[[], float] = time.time,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if failure_ttl_seconds <= 0:
            raise ValueError("failure_ttl_seconds must be positive")
        self._fetcher = fetcher
        self._ttl = ttl_seconds
        self._failure_ttl = failure_ttl_seconds
        self._cache_dir = cache_dir
        self._clock = clock_fn
        self._wallclock = wallclock_fn
        self._entries: dict[str, _CachedEntry] = {}
        self._global_lock = threading.Lock()
        self._host_locks: dict[str, threading.Lock] = {}
        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)

    # -- Public API ---------------------------------------------------

    def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
        cache_key = _cache_key(url, user_agent)
        entry = self._get_or_fetch(cache_key=cache_key, url=url, user_agent=user_agent)
        if entry.status == _FETCH_FAILURE_STATUS:
            # Cached fetch failure: fail-closed but don't re-issue.
            return RobotsAdvice(
                is_allowed=False,
                disallow_reason="robots.txt unavailable; cooperative crawler defaults to disallow",
            )
        return _advice_from_parser(
            entry.parser, url=url, user_agent=user_agent, status=entry.status
        )

    # -- Cache plumbing ----------------------------------------------

    def _get_or_fetch(
        self,
        *,
        cache_key: str,
        url: str,
        user_agent: str,
    ) -> _CachedEntry:
        # Per-(host, ua) lock so concurrent ``evaluate`` calls collapse
        # into a single fetch (design: fetch-once-per-host). The cache
        # key includes the user-agent because origins can serve UA-
        # specific robots.txt — sharing a parser across UAs would mix
        # rule sets and violate the single-source-of-truth UA contract
        # (codex iter-1 important).
        host_lock = self._lock_for_key(cache_key)
        with host_lock:
            now = self._clock()
            cached = self._entries.get(cache_key)
            if cached is not None and not self._is_expired(cached, now=now):
                return cached
            disk_entry = self._read_disk_cache(cache_key=cache_key, now=now)
            if disk_entry is not None:
                self._entries[cache_key] = disk_entry
                return disk_entry
            entry = self._fetch_with_fallback(url=url, user_agent=user_agent)
            self._entries[cache_key] = entry
            self._write_disk_cache(cache_key=cache_key, entry=entry)
            return entry

    def _is_expired(self, entry: _CachedEntry, *, now: float) -> bool:
        ttl = self._failure_ttl if entry.status == _FETCH_FAILURE_STATUS else self._ttl
        return (now - entry.fetched_at) >= ttl

    def _lock_for_key(self, cache_key: str) -> threading.Lock:
        with self._global_lock:
            lock = self._host_locks.get(cache_key)
            if lock is None:
                lock = threading.Lock()
                self._host_locks[cache_key] = lock
            return lock

    def _fetch_with_fallback(self, *, url: str, user_agent: str) -> _CachedEntry:
        robots_url = _robots_url_for(url)
        try:
            result = self._fetcher(robots_url, user_agent)
        except Exception as exc:  # noqa: BLE001 — fail-closed on any fetcher error
            _logger.warning(
                "robots.txt fetch failed; fail-closed",
                robots_url=robots_url,
                error_type=type(exc).__name__,
            )
            # Cache the failure with a short TTL so subsequent
            # ``evaluate`` calls during an outage short-circuit instead
            # of re-issuing the failing request (codex iter-2
            # important: fetch-once-per-host must hold under failure
            # too). Synthesise a disallow-all parser so any read still
            # fails closed.
            failure_parser = _build_parser(
                robots_url=robots_url, status=_FETCH_FAILURE_STATUS, body=""
            )
            return _CachedEntry(
                parser=failure_parser,
                fetched_at=self._clock(),
                fetched_at_wallclock=self._wallclock(),
                status=_FETCH_FAILURE_STATUS,
                robots_url=robots_url,
                body=None,
            )
        parser = _build_parser(robots_url=robots_url, status=result.status, body=result.body)
        # Preserve the original body for synthesised parsers as ``None``
        # (404 → allow-all, 5xx → disallow-all). For 200 responses the
        # exact bytes are kept so the on-disk cache round-trips
        # faithfully (codex iter-1 important).
        body_for_cache: str | None = result.body if 200 <= result.status < 300 else None
        return _CachedEntry(
            parser=parser,
            fetched_at=self._clock(),
            fetched_at_wallclock=self._wallclock(),
            status=result.status,
            robots_url=robots_url,
            body=body_for_cache,
        )

    # -- On-disk cache ------------------------------------------------

    def _disk_paths(self, cache_key: str) -> tuple[Path, Path] | None:
        if self._cache_dir is None:
            return None
        safe = _safe_filename(cache_key)
        return (
            self._cache_dir / f"{safe}{_BODY_SUFFIX}",
            self._cache_dir / f"{safe}{_META_SUFFIX}",
        )

    def _read_disk_cache(self, *, cache_key: str, now: float) -> _CachedEntry | None:
        paths = self._disk_paths(cache_key)
        if paths is None:
            return None
        body_path, meta_path = paths
        if not meta_path.exists():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            status = int(meta["status"])
            fetched_at_wallclock = float(meta["fetched_at_wallclock"])
            robots_url = str(meta["robots_url"])
        except (OSError, ValueError, KeyError):
            return None
        # TTL math against persisted entries uses wall-clock so it is
        # valid across process restarts (codex iter-2 important —
        # ``monotonic`` is process-relative and was previously
        # persisted in error).
        wall_now = self._wallclock()
        elapsed_wall = wall_now - fetched_at_wallclock
        ttl = self._failure_ttl if status == _FETCH_FAILURE_STATUS else self._ttl
        if elapsed_wall < 0 or elapsed_wall >= ttl:
            return None
        # Body file may be absent for synthesised parsers (404 / 5xx
        # caches don't preserve a body — see ``body_for_cache`` above).
        body: str | None = None
        if body_path.exists():
            try:
                body = body_path.read_text(encoding="utf-8")
            except OSError:
                return None
        parser = _build_parser(robots_url=robots_url, status=status, body=body or "")
        # Project the wall-clock age back onto the in-memory monotonic
        # clock so the in-memory TTL math behaves identically whether
        # the entry came from disk or from a live fetch.
        return _CachedEntry(
            parser=parser,
            fetched_at=now - elapsed_wall,
            fetched_at_wallclock=fetched_at_wallclock,
            status=status,
            robots_url=robots_url,
            body=body,
        )

    def _write_disk_cache(self, *, cache_key: str, entry: _CachedEntry) -> None:
        paths = self._disk_paths(cache_key)
        if paths is None:
            return
        body_path, meta_path = paths
        try:
            if entry.body is not None:
                # Preserve the original fetched body verbatim — ``str``
                # of ``RobotFileParser`` is a parser-state rendering and
                # may drop comments / unknown directives, so it is not
                # a faithful round-trip (codex iter-1 important).
                body_path.write_text(entry.body, encoding="utf-8")
            else:
                # Synthesised parser (404 / 5xx / fetch-failure) —
                # clean up any prior body file so reads see "absent"
                # consistently.
                if body_path.exists():
                    body_path.unlink()
            meta_path.write_text(
                json.dumps(
                    {
                        "status": entry.status,
                        "fetched_at_wallclock": entry.fetched_at_wallclock,
                        "robots_url": entry.robots_url,
                    }
                ),
                encoding="utf-8",
            )
        except OSError as exc:
            _logger.warning(
                "robots.txt on-disk cache write failed",
                cache_key=cache_key,
                error_type=type(exc).__name__,
            )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _host_key(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}".lower()


def _cache_key(url: str, user_agent: str) -> str:
    """Cache key combining host and user-agent.

    Origins can serve UA-specific ``robots.txt`` (Google's spec
    permits per-UA groups). Sharing a parser across UAs would mix
    rule sets and silently violate the single-source-of-truth UA
    contract — codex iter-1 important. Including the UA forces a
    fresh fetch when the run's UA differs from a previously cached
    one, which is the conservative behavior for a cooperative
    crawler.
    """

    return f"{_host_key(url)}|ua={user_agent}"


def _robots_url_for(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))


def _safe_filename(cache_key: str) -> str:
    # Hash to keep the on-disk filename short and avoid path traversal
    # via UA strings that could contain ``/`` or other separator
    # characters. The hash is used purely as a stable key — collisions
    # would only mean a fresh re-fetch.
    digest = hashlib.sha1(cache_key.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]
    return digest


def _build_parser(*, robots_url: str, status: int, body: str) -> RobotFileParser:
    parser = RobotFileParser(robots_url)
    if status == _FETCH_FAILURE_STATUS:
        # Cached fetch-failure marker: synthesise a disallow-all parser
        # so any read fails closed even before the wrapper checks the
        # status sentinel.
        parser.parse(["User-agent: *", "Disallow: /"])
        return parser
    if status == 404:
        # IETF guidance: 404 means "no rules" → allow all. We achieve
        # this by feeding an empty rule set.
        parser.parse([])
        return parser
    if status >= 500 or status >= 400:
        # 5xx (and other 4xx that aren't 404) → fail closed: produce a
        # parser that disallows everything.
        parser.parse(["User-agent: *", "Disallow: /"])
        return parser
    parser.parse(body.splitlines())
    return parser


# ``_serialise_parser`` was removed in favor of writing the original
# fetched body directly (see ``_CachedEntry.body`` and
# ``_write_disk_cache``) — codex iter-1 important: parser ``__str__``
# is a state rendering and was not a faithful round-trip.


def _advice_from_parser(
    parser: RobotFileParser,
    *,
    url: str,
    user_agent: str,
    status: int,
) -> RobotsAdvice:
    is_allowed = parser.can_fetch(user_agent, url)
    crawl_delay_raw = parser.crawl_delay(user_agent)
    crawl_delay = float(crawl_delay_raw) if crawl_delay_raw is not None else None
    request_rate_obj = parser.request_rate(user_agent)
    request_rate: tuple[int, int] | None = None
    if request_rate_obj is not None:
        request_rate = (
            int(request_rate_obj.requests),
            int(request_rate_obj.seconds),
        )
    if is_allowed:
        return RobotsAdvice(
            is_allowed=True,
            crawl_delay=crawl_delay,
            request_rate=request_rate,
        )
    return RobotsAdvice(
        is_allowed=False,
        crawl_delay=crawl_delay,
        request_rate=request_rate,
        disallow_reason=f"robots.txt status={status}; user-agent={user_agent} disallowed",
    )


def make_httpx_robots_fetcher(
    *,
    timeout_s: float = 10.0,
    transport: httpx.BaseTransport | None = None,
) -> RobotsFetcher:
    """Production-grade robots.txt fetcher.

    Returns a callable that satisfies :data:`RobotsFetcher`. The
    returned fetcher uses a **dedicated** :class:`httpx.Client` that
    does **not** consult any :class:`RobotsPort` — this is the only
    way to break the recursion otherwise implied by
    "fetch ``robots.txt`` before fetching anything else"
    (codex iter-2 critical). Callers must not wire
    :class:`StdlibHttpSourceAdapter` here: that adapter now consults
    :class:`RobotsPort` before every fetch, so using it to retrieve
    ``/robots.txt`` would loop.

    The fetcher honors the ``user_agent`` argument (so the single
    source-of-truth UA is preserved end to end) and a small per-request
    timeout. It does not implement retries, redirect following, or
    the broader :class:`StdlibHttpSourceAdapter` policy machinery —
    those layers belong to the caller-side fetch, not to robots
    discovery. Network-level failures and non-2xx responses are
    surfaced via :class:`RobotsFetchResult` so the caller's fail-closed
    semantics apply uniformly.
    """

    def fetch(robots_url: str, user_agent: str) -> RobotsFetchResult:
        client_kwargs: dict[str, object] = {
            "timeout": httpx.Timeout(timeout_s),
            "headers": {"User-Agent": user_agent},
            "follow_redirects": False,
        }
        if transport is not None:
            client_kwargs["transport"] = transport
        with httpx.Client(**client_kwargs) as client:  # type: ignore[arg-type]
            response = client.get(robots_url)
            return RobotsFetchResult(status=int(response.status_code), body=response.text)

    return fetch


__all__ = [
    "RobotsFetchResult",
    "RobotsFetcher",
    "UrllibRobotsParser",
    "make_httpx_robots_fetcher",
]
