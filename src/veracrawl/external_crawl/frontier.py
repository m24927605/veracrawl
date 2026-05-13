"""In-memory frontier scheduler for the external crawl runtime.

The frontier is the single source of truth for which URLs have been
seen, which are pending, and why others were skipped. Every state
transition is captured as a :class:`FrontierEvent` so the run report
and the events log can reconstruct lineage without inferring it from
the artifact tree.

Design notes:

* The frontier is pure (no network I/O). Robots checks, fetches, and
  rate limiting happen outside; callers report robots denials back
  via :meth:`skip` so failures land in the same skip-reason taxonomy
  as the in-frontier filter outcomes.
* Deduplication is by canonical URL — :func:`url.canonicalize_url`
  collapses ``HTTPS://Host/p`` and ``https://host:443/p`` to the
  same key.
* ``max_pages`` is a *fetch* budget. Admissions keep flowing until
  :meth:`pop` refuses; that lets the caller distinguish "we admitted
  many candidates but only fetched two" from "we admitted two".
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from veracrawl.external_crawl.url import (
    DomainFilterReason,
    canonicalize_url,
    classify_url,
)


class SkipReason(StrEnum):
    OUTSIDE_ALLOWED_DOMAIN = "outside_allowed_domain"
    DENIED_DOMAIN = "denied_domain"
    UNSUPPORTED_SCHEME = "unsupported_scheme"
    PRIVATE_NETWORK_DENIED = "private_network_denied"
    DEPTH_EXCEEDED = "depth_exceeded"
    DUPLICATE = "duplicate"
    BUDGET_EXCEEDED = "budget_exceeded"
    ROBOTS_DENIED = "robots_denied"


_DOMAIN_REASON_MAP = {
    DomainFilterReason.OUTSIDE_ALLOWED_DOMAIN: SkipReason.OUTSIDE_ALLOWED_DOMAIN,
    DomainFilterReason.DENIED_DOMAIN: SkipReason.DENIED_DOMAIN,
    DomainFilterReason.UNSUPPORTED_SCHEME: SkipReason.UNSUPPORTED_SCHEME,
    DomainFilterReason.PRIVATE_NETWORK_DENIED: SkipReason.PRIVATE_NETWORK_DENIED,
}


@dataclass(frozen=True, slots=True)
class FrontierItem:
    canonical_url: str
    depth: int
    parent_canonical_url: str | None
    discovered_at: datetime


@dataclass(frozen=True, slots=True)
class EnqueueOutcome:
    admitted: bool
    canonical_url: str | None
    skip_reason: SkipReason | None


@dataclass(frozen=True, slots=True)
class FrontierEvent:
    kind: str  # "enqueued" | "skipped" | "dequeued" | "fetched"
    canonical_url: str | None
    depth: int | None
    skip_reason: SkipReason | None
    occurred_at: datetime


@dataclass(slots=True)
class FrontierCounters:
    enqueued: int = 0
    fetched: int = 0
    skipped_by_reason: Counter[SkipReason] = field(default_factory=Counter)


def _now() -> datetime:
    return datetime.now(tz=UTC)


class ExternalCrawlFrontier:
    def __init__(
        self,
        *,
        allowed_domains: frozenset[str],
        denied_domains: frozenset[str],
        max_depth: int,
        max_pages: int,
        allow_loopback: bool = False,
    ) -> None:
        if max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        if max_pages < 1:
            raise ValueError("max_pages must be positive")
        self._allowed_domains = allowed_domains
        self._denied_domains = denied_domains
        self._max_depth = max_depth
        self._max_pages = max_pages
        self._allow_loopback = allow_loopback

        self._queue: deque[FrontierItem] = deque()
        self._seen: set[str] = set()
        self._fetched: set[str] = set()
        self._events: list[FrontierEvent] = []
        self._counters = FrontierCounters()

    def enqueue(
        self,
        url: str,
        *,
        depth: int,
        parent_canonical_url: str | None = None,
    ) -> EnqueueOutcome:
        try:
            decision = classify_url(
                url,
                allowed_domains=self._allowed_domains,
                denied_domains=self._denied_domains,
                allow_loopback=self._allow_loopback,
            )
        except ValueError:
            return self._record_skip(
                None, SkipReason.UNSUPPORTED_SCHEME, depth=depth
            )

        if not decision.admit:
            assert decision.reason is not None
            return self._record_skip(
                decision.canonical_url,
                _DOMAIN_REASON_MAP[decision.reason],
                depth=depth,
            )

        canonical = decision.canonical_url
        assert canonical is not None

        if depth > self._max_depth:
            return self._record_skip(canonical, SkipReason.DEPTH_EXCEEDED, depth=depth)

        if canonical in self._seen:
            return self._record_skip(canonical, SkipReason.DUPLICATE, depth=depth)

        item = FrontierItem(
            canonical_url=canonical,
            depth=depth,
            parent_canonical_url=parent_canonical_url,
            discovered_at=_now(),
        )
        self._seen.add(canonical)
        self._queue.append(item)
        self._counters.enqueued += 1
        self._events.append(
            FrontierEvent(
                kind="enqueued",
                canonical_url=canonical,
                depth=depth,
                skip_reason=None,
                occurred_at=item.discovered_at,
            )
        )
        return EnqueueOutcome(admitted=True, canonical_url=canonical, skip_reason=None)

    def pop(self) -> FrontierItem | None:
        if self.budget_exhausted():
            return None
        if not self._queue:
            return None
        item = self._queue.popleft()
        self._events.append(
            FrontierEvent(
                kind="dequeued",
                canonical_url=item.canonical_url,
                depth=item.depth,
                skip_reason=None,
                occurred_at=_now(),
            )
        )
        return item

    def mark_fetched(self, canonical_url: str) -> None:
        if canonical_url in self._fetched:
            return
        self._fetched.add(canonical_url)
        self._counters.fetched += 1
        self._events.append(
            FrontierEvent(
                kind="fetched",
                canonical_url=canonical_url,
                depth=None,
                skip_reason=None,
                occurred_at=_now(),
            )
        )

    def skip(self, canonical_url: str, reason: SkipReason) -> None:
        self._record_skip(canonical_url, reason, depth=None)

    def budget_exhausted(self) -> bool:
        return self._counters.fetched >= self._max_pages

    def counters(self) -> FrontierCounters:
        return self._counters

    def events(self) -> list[FrontierEvent]:
        return list(self._events)

    def _record_skip(
        self,
        canonical_url: str | None,
        reason: SkipReason,
        *,
        depth: int | None,
    ) -> EnqueueOutcome:
        self._counters.skipped_by_reason[reason] += 1
        self._events.append(
            FrontierEvent(
                kind="skipped",
                canonical_url=canonical_url,
                depth=depth,
                skip_reason=reason,
                occurred_at=_now(),
            )
        )
        return EnqueueOutcome(
            admitted=False, canonical_url=canonical_url, skip_reason=reason
        )


# Re-export the canonical URL helper as a convenience for callers
# that want to compute a key before enqueueing.
def canonical_for(url: str) -> str:
    return canonicalize_url(url)


__all__ = [
    "EnqueueOutcome",
    "ExternalCrawlFrontier",
    "FrontierCounters",
    "FrontierEvent",
    "FrontierItem",
    "SkipReason",
    "canonical_for",
]
