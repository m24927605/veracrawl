"""Protocol describing the frontier surface the runner depends on.

Introduced by s3.1 (``docs/plans/general-purpose-crawler-agentification/
s3.1-priority-queue-frontier.md``) so the runner can accept either the
legacy FIFO ``ExternalCrawlFrontier`` or the new
``PriorityCrawlFrontier`` via a single ctor arg without importing the
priority adapter itself.

Only the methods the runner actually calls are pinned. ``add_hints`` is
intentionally absent from the Protocol: the runner uses
``hasattr(frontier, "add_hints")`` so the legacy FIFO frontier (which
doesn't implement it) is unaffected.
"""

from __future__ import annotations

from typing import Protocol

from veracrawl.external_crawl.frontier import (
    EnqueueOutcome,
    FrontierCounters,
    FrontierEvent,
    FrontierItem,
    SkipReason,
)


class FrontierLike(Protocol):
    def enqueue(
        self, url: str, *, depth: int, parent_canonical_url: str | None = None,
    ) -> EnqueueOutcome: ...

    def pop(self) -> FrontierItem | None: ...

    def mark_fetched(self, canonical_url: str) -> None: ...

    def skip(self, canonical_url: str, reason: SkipReason) -> None: ...

    def budget_exhausted(self) -> bool: ...

    def counters(self) -> FrontierCounters: ...

    def events(self) -> list[FrontierEvent]: ...


__all__ = ["FrontierLike"]
