"""``ReplayingHttpFetcher`` — replay-side ``CrawlHttpFetcherPort`` (s12).

Substitutes recorded ``FetchOutcome`` values for live HTTP calls.
The caller pre-resolves the bundle's ``fetch_outcome_refs`` into
concrete ``FetchOutcome`` instances and hands them in as
``outcomes_by_url`` (per R2 reservation: full FetchOutcome
materialization, not just a Ref).

* **Strict mode** (default): missing URL raises
  ``ReplayBundleLookupMissError`` — the recorded run touched a
  URL the bundle didn't capture, which is a wiring bug.
* **Permissive mode**: missing URL falls through to the wrapped
  live fetcher. Useful for hybrid record-then-extend scenarios.

See ``docs/plans/general-purpose-crawler-agentification/
s12-runner-replay-wiring.md``.
"""

from __future__ import annotations

from collections.abc import Mapping

from veracrawl.contracts.errors import ReplayBundleLookupMissError
from veracrawl.ports.crawl_http_fetcher import (
    CrawlHttpFetcherPort,
    FetchOutcome,
)


class ReplayingHttpFetcher:
    def __init__(
        self,
        *,
        outcomes_by_url: Mapping[str, FetchOutcome],
        wrapped: CrawlHttpFetcherPort | None = None,
        strict: bool = True,
    ) -> None:
        self._outcomes_by_url: dict[str, FetchOutcome] = dict(outcomes_by_url)
        self._wrapped = wrapped
        self._strict = strict
        self.invocation_count = 0

    def fetch(self, url: str, *, timeout_seconds: float) -> FetchOutcome:
        self.invocation_count += 1
        if url in self._outcomes_by_url:
            return self._outcomes_by_url[url]
        if self._strict or self._wrapped is None:
            raise ReplayBundleLookupMissError(
                category="fetch_outcome", key=url,
            )
        return self._wrapped.fetch(url, timeout_seconds=timeout_seconds)


__all__ = ["ReplayingHttpFetcher"]
