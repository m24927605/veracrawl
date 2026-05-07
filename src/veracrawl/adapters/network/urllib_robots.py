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

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Final
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from veracrawl.ports.robots import RobotsAdvice
from veracrawl.runtime_support.logging import get_logger

_logger = get_logger(__name__)

_DEFAULT_TTL_SECONDS: Final[float] = 3600.0
_META_SUFFIX: Final[str] = ".meta.json"
_BODY_SUFFIX: Final[str] = ".robots.txt"


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
    fetched_at: float
    status: int
    # Track the robots URL alongside the parser. ``RobotFileParser`` does
    # carry an ``url`` attribute at runtime (set in ``__init__`` /
    # ``set_url``) but it isn't in the typeshed stubs, so we keep our
    # own copy to satisfy ``mypy --strict`` without ``# type: ignore``.
    robots_url: str


class UrllibRobotsParser:
    """``RobotsPort`` impl using ``urllib.robotparser.RobotFileParser``.

    Construction parameters:

    * ``fetcher``: callable that fetches ``robots.txt`` for a given
      ``robots_url`` using a given ``user_agent``. The fetcher is
      injected so the parser is testable and so callers can wire it to
      whatever transport the run uses (``StdlibHttpSourceAdapter`` for
      production, a fake for tests).
    * ``ttl_seconds``: in-memory + on-disk cache TTL. Defaults to one
      hour, the same order of magnitude most well-behaved crawlers
      use.
    * ``cache_dir``: optional directory for the on-disk cache. ``None``
      means "in-memory only" (still fetch-once-per-host per process).
    * ``clock_fn``: monotonic-time injection for tests.
    """

    def __init__(
        self,
        *,
        fetcher: RobotsFetcher,
        ttl_seconds: float = _DEFAULT_TTL_SECONDS,
        cache_dir: Path | None = None,
        clock_fn: Callable[[], float] = monotonic,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._fetcher = fetcher
        self._ttl = ttl_seconds
        self._cache_dir = cache_dir
        self._clock = clock_fn
        self._entries: dict[str, _CachedEntry] = {}
        self._global_lock = threading.Lock()
        self._host_locks: dict[str, threading.Lock] = {}
        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)

    # -- Public API ---------------------------------------------------

    def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
        host_key = _host_key(url)
        entry = self._get_or_fetch(host_key=host_key, url=url, user_agent=user_agent)
        if entry is None:
            # Failure to fetch and to recover from disk → fail closed.
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
        host_key: str,
        url: str,
        user_agent: str,
    ) -> _CachedEntry | None:
        # Per-host lock so concurrent ``evaluate`` calls collapse to a
        # single fetch (design: fetch-once-per-host).
        host_lock = self._lock_for_host(host_key)
        with host_lock:
            cached = self._entries.get(host_key)
            now = self._clock()
            if cached is not None and (now - cached.fetched_at) < self._ttl:
                return cached
            disk_entry = self._read_disk_cache(host_key=host_key, now=now)
            if disk_entry is not None:
                self._entries[host_key] = disk_entry
                return disk_entry
            fetched = self._fetch_with_fallback(url=url, user_agent=user_agent)
            if fetched is None:
                return None
            self._entries[host_key] = fetched
            self._write_disk_cache(host_key=host_key, entry=fetched)
            return fetched

    def _lock_for_host(self, host_key: str) -> threading.Lock:
        with self._global_lock:
            lock = self._host_locks.get(host_key)
            if lock is None:
                lock = threading.Lock()
                self._host_locks[host_key] = lock
            return lock

    def _fetch_with_fallback(self, *, url: str, user_agent: str) -> _CachedEntry | None:
        robots_url = _robots_url_for(url)
        try:
            result = self._fetcher(robots_url, user_agent)
        except Exception as exc:  # noqa: BLE001 — fail-closed on any fetcher error
            _logger.warning(
                "robots.txt fetch failed; fail-closed",
                robots_url=robots_url,
                error_type=type(exc).__name__,
            )
            return None
        parser = _build_parser(robots_url=robots_url, status=result.status, body=result.body)
        return _CachedEntry(
            parser=parser,
            fetched_at=self._clock(),
            status=result.status,
            robots_url=robots_url,
        )

    # -- On-disk cache ------------------------------------------------

    def _disk_paths(self, host_key: str) -> tuple[Path, Path] | None:
        if self._cache_dir is None:
            return None
        safe = _safe_filename(host_key)
        return (
            self._cache_dir / f"{safe}{_BODY_SUFFIX}",
            self._cache_dir / f"{safe}{_META_SUFFIX}",
        )

    def _read_disk_cache(self, *, host_key: str, now: float) -> _CachedEntry | None:
        paths = self._disk_paths(host_key)
        if paths is None:
            return None
        body_path, meta_path = paths
        if not body_path.exists() or not meta_path.exists():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            status = int(meta["status"])
            fetched_at = float(meta["fetched_at"])
            robots_url = str(meta["robots_url"])
            body = body_path.read_text(encoding="utf-8")
        except (OSError, ValueError, KeyError):
            return None
        if (now - fetched_at) >= self._ttl:
            return None
        parser = _build_parser(robots_url=robots_url, status=status, body=body)
        return _CachedEntry(
            parser=parser,
            fetched_at=fetched_at,
            status=status,
            robots_url=robots_url,
        )

    def _write_disk_cache(self, *, host_key: str, entry: _CachedEntry) -> None:
        paths = self._disk_paths(host_key)
        if paths is None:
            return
        body_path, meta_path = paths
        try:
            body_path.write_text(_serialise_parser(entry.parser), encoding="utf-8")
            meta_path.write_text(
                json.dumps(
                    {
                        "status": entry.status,
                        "fetched_at": entry.fetched_at,
                        "robots_url": entry.robots_url,
                    }
                ),
                encoding="utf-8",
            )
        except OSError as exc:
            _logger.warning(
                "robots.txt on-disk cache write failed",
                host_key=host_key,
                error_type=type(exc).__name__,
            )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _host_key(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}".lower()


def _robots_url_for(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))


def _safe_filename(host_key: str) -> str:
    return host_key.replace("://", "__").replace("/", "_").replace(":", "_")


def _build_parser(*, robots_url: str, status: int, body: str) -> RobotFileParser:
    parser = RobotFileParser(robots_url)
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


def _serialise_parser(parser: RobotFileParser) -> str:
    """Best-effort serialisation of the parser back to text for disk cache.

    ``RobotFileParser`` exposes ``__str__`` which renders parsed rules
    in a robots.txt-compatible form. We use it directly so the disk
    payload is human-readable and the parsing path on next load is
    identical to the live fetch path.
    """

    return str(parser)


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


__all__ = [
    "RobotsFetchResult",
    "RobotsFetcher",
    "UrllibRobotsParser",
]
