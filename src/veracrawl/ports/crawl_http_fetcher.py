"""``CrawlHttpFetcherPort`` — narrow HTTP transport for the external crawl runtime.

Core depends on this Protocol; concrete implementations (e.g.,
``veracrawl.adapters.network.httpx_crawl_fetcher.HttpxCrawlFetcher``)
live in ``adapters/`` so the runtime stays framework-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class FetchError(RuntimeError):
    """Raised when a fetch is refused before or during transport."""


@dataclass(frozen=True, slots=True)
class FetchOutcome:
    requested_url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    body: bytes
    content_type: str
    redirect_chain: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


class CrawlHttpFetcherPort(Protocol):
    def fetch(self, url: str, *, timeout_seconds: float) -> FetchOutcome: ...


__all__ = ["CrawlHttpFetcherPort", "FetchError", "FetchOutcome"]
