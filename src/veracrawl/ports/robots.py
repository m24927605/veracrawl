"""``RobotsPort`` — robots.txt evaluation hexagonal port.

The cooperative HTTP / browser paths must consult ``robots.txt`` for
every initial URL and every cross-redirect target before issuing the
fetch (design.md §4 Phase 1: "enforce on initial URL **and** every
redirect target"). Phase 1 step 1.2 introduces this port so the
adapters depend on a stable surface; the default production impl is
``UrllibRobotsParser`` (``adapters/network/urllib_robots.py``), and
the framework default is :class:`NoopRobotsPort` so existing tests
keep passing without configuration (Phase 1 boundary acceptance).

The port returns a :class:`RobotsAdvice` payload for every evaluation.
``is_allowed`` decides whether the URL may be fetched at all;
``crawl_delay`` / ``request_rate`` are the per-host floor inputs Phase
1 step 1.3 ``RateLimiterPort`` consumes (``floor = strictest of
Retry-After / crawl_delay / request_rate``). The combined struct keeps
callers from forgetting any of the three robot signals — an unparsed
delay / rate is communicated as ``None``, never silently coerced to
zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class RobotsAdvice:
    """The robots.txt evaluation result for one URL.

    Attributes:
        is_allowed: ``True`` when the active user-agent is permitted to
            fetch the URL by ``robots.txt``. ``False`` means the
            adapter must raise ``RobotsBlockedError`` and not retry.
        crawl_delay: ``Crawl-delay`` directive value (seconds) for the
            user-agent / wildcard group. ``None`` if the file did not
            specify one. The rate limiter floors at the strictest of
            this, ``request_rate``, and ``Retry-After`` (design §4).
        request_rate: ``Request-rate`` directive parsed as
            ``(requests, seconds)``. ``None`` if absent.
        disallow_reason: Optional human-readable reason populated when
            ``is_allowed=False`` (e.g., ``"Disallow: /admin"``). Used
            only for diagnostics; the orchestrator decision must be
            driven by ``is_allowed``.
    """

    is_allowed: bool
    crawl_delay: float | None = None
    request_rate: tuple[int, int] | None = None
    disallow_reason: str | None = None


@runtime_checkable
class RobotsPort(Protocol):
    """Hexagonal port for ``robots.txt`` evaluation.

    Implementations are responsible for fetching, caching, and parsing
    ``robots.txt`` per host (design specifies fetch-once-per-host with
    TTL + on-disk cache for the production default
    :class:`~veracrawl.adapters.network.urllib_robots.UrllibRobotsParser`).

    The same ``user_agent`` string must be used to fetch ``robots.txt``
    and to evaluate URLs against it — that is the "single source-of-
    truth UA" requirement in design.md §4 Phase 1, otherwise an origin
    serving UA-specific rules can serve permissive rules to one UA and
    receive traffic with a different UA.
    """

    def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
        """Return the robots.txt advice for ``url`` and ``user_agent``."""
        ...


class NoopRobotsPort:
    """Permissive default — every URL is allowed, no delay / rate.

    Used when no robots port is configured (the boundary acceptance
    requires existing tests to pass without configuration). Production
    callers must inject :class:`UrllibRobotsParser` (or another real
    impl); leaving the no-op in production is a wiring bug, not a
    permissive policy.
    """

    def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
        del url, user_agent
        return RobotsAdvice(is_allowed=True)
