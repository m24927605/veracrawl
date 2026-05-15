"""Priority-queue frontier scheduler for the external crawl runtime.

Heap-based variant of :class:`ExternalCrawlFrontier` (FIFO) that pops
items by ``(-priority_score, enqueue_seq)`` so the planner's
``FrontierPriorityHint`` set actually steers the crawl. Same admission
rules, same skip taxonomy, same event log — only the pop order
changes.

Hints are mutable: :meth:`add_hints` appends new hints and re-heapifies
every queued item under the union of all hints to date. The runner
calls this after the s3 initial plan and after each s6 replan so
freshly-discovered hint state is binding from the next pop onwards.

Introduced by s3.1 (``docs/plans/general-purpose-crawler-agentification/
s3.1-priority-queue-frontier.md``).
"""

from __future__ import annotations

import fnmatch
import heapq
from datetime import UTC, datetime
from urllib.parse import urlparse

from veracrawl.contracts.crawl_planner import FrontierPriorityHint
from veracrawl.contracts.enums import FrontierMatchKind
from veracrawl.external_crawl.frontier import (
    EnqueueOutcome,
    FrontierCounters,
    FrontierEvent,
    FrontierItem,
    SkipReason,
)
from veracrawl.external_crawl.url import (
    DomainFilterReason,
    canonicalize_url,
    classify_url,
)

_PRIORITY_CLAMP_MAX = 2.0
_PRIORITY_CLAMP_MIN = -2.0

_DOMAIN_REASON_MAP = {
    DomainFilterReason.OUTSIDE_ALLOWED_DOMAIN: SkipReason.OUTSIDE_ALLOWED_DOMAIN,
    DomainFilterReason.DENIED_DOMAIN: SkipReason.DENIED_DOMAIN,
    DomainFilterReason.UNSUPPORTED_SCHEME: SkipReason.UNSUPPORTED_SCHEME,
    DomainFilterReason.PRIVATE_NETWORK_DENIED: SkipReason.PRIVATE_NETWORK_DENIED,
}


def _now() -> datetime:
    return datetime.now(tz=UTC)


def compute_item_priority(
    *,
    canonical_url: str,
    depth: int,
    hints: list[FrontierPriorityHint],
) -> float:
    """Pure function — same inputs always produce same output."""

    base = 1.0 / (1.0 + depth)
    hostname = urlparse(canonical_url).hostname or ""
    score = base
    for hint in hints:
        if hint.match_kind is FrontierMatchKind.URL_PREFIX:
            if canonical_url.startswith(hint.match_value):
                score += hint.priority_delta
        elif hint.match_kind is FrontierMatchKind.HOST_GLOB:
            if hostname and fnmatch.fnmatch(hostname, hint.match_value):
                score += hint.priority_delta
        # CONTENT_TYPE_PREFIX: pre-fetch content-type is unknown at
        # enqueue time; recorded by add_hints but inert here.
    return max(_PRIORITY_CLAMP_MIN, min(_PRIORITY_CLAMP_MAX, score))


class PriorityCrawlFrontier:
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

        # Each heap entry: (neg_priority, enqueue_seq, FrontierItem).
        self._heap: list[tuple[float, int, FrontierItem]] = []
        self._enqueue_seq = 0
        self._seen: set[str] = set()
        self._fetched: set[str] = set()
        self._events: list[FrontierEvent] = []
        self._counters = FrontierCounters()
        self._hints: list[FrontierPriorityHint] = []

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
                None, SkipReason.UNSUPPORTED_SCHEME, depth=depth,
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
            return self._record_skip(
                canonical, SkipReason.DEPTH_EXCEEDED, depth=depth,
            )
        if canonical in self._seen:
            return self._record_skip(canonical, SkipReason.DUPLICATE, depth=depth)
        item = FrontierItem(
            canonical_url=canonical,
            depth=depth,
            parent_canonical_url=parent_canonical_url,
            discovered_at=_now(),
        )
        self._seen.add(canonical)
        priority = compute_item_priority(
            canonical_url=canonical, depth=depth, hints=self._hints,
        )
        heapq.heappush(
            self._heap, (-priority, self._enqueue_seq, item),
        )
        self._enqueue_seq += 1
        self._counters.enqueued += 1
        self._events.append(
            FrontierEvent(
                kind="enqueued",
                canonical_url=canonical,
                depth=depth,
                skip_reason=None,
                occurred_at=item.discovered_at,
            ),
        )
        return EnqueueOutcome(
            admitted=True, canonical_url=canonical, skip_reason=None,
        )

    def pop(self) -> FrontierItem | None:
        if self.budget_exhausted():
            return None
        if not self._heap:
            return None
        _, _, item = heapq.heappop(self._heap)
        self._events.append(
            FrontierEvent(
                kind="dequeued",
                canonical_url=item.canonical_url,
                depth=item.depth,
                skip_reason=None,
                occurred_at=_now(),
            ),
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
            ),
        )

    def skip(self, canonical_url: str, reason: SkipReason) -> None:
        self._record_skip(canonical_url, reason, depth=None)

    def budget_exhausted(self) -> bool:
        return self._counters.fetched >= self._max_pages

    def counters(self) -> FrontierCounters:
        return self._counters

    def events(self) -> list[FrontierEvent]:
        return list(self._events)

    def add_hints(self, new_hints: list[FrontierPriorityHint]) -> None:
        """Append hints and re-prioritize every queued item.

        Called by the runner after the initial plan and after each
        s6 replan. Re-heapifies under the union of all hints so the
        next pop respects the freshly-derived state.
        """

        if not new_hints:
            return
        self._hints.extend(new_hints)
        rebuilt: list[tuple[float, int, FrontierItem]] = []
        for _, seq, item in self._heap:
            priority = compute_item_priority(
                canonical_url=item.canonical_url,
                depth=item.depth,
                hints=self._hints,
            )
            rebuilt.append((-priority, seq, item))
        heapq.heapify(rebuilt)
        self._heap = rebuilt

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
            ),
        )
        return EnqueueOutcome(
            admitted=False, canonical_url=canonical_url, skip_reason=reason,
        )


def canonical_for(url: str) -> str:
    return canonicalize_url(url)


__all__ = [
    "PriorityCrawlFrontier",
    "canonical_for",
    "compute_item_priority",
]
