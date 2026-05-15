"""Unit tests for ``ReplayingHttpFetcher`` (s12)."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from veracrawl.adapters.network.replaying_http_fetcher import (
    ReplayingHttpFetcher,
)
from veracrawl.contracts.errors import ReplayBundleLookupMissError
from veracrawl.ports.crawl_http_fetcher import FetchOutcome


def _outcome(url: str = "https://a.example/1") -> FetchOutcome:
    return FetchOutcome(
        requested_url=url, final_url=url, status_code=200,
        headers={"content-type": "text/html"},
        body=b"<html></html>", content_type="text/html",
    )


@dataclass
class _LiveFetcher:
    calls: list[str] = field(default_factory=list)

    def fetch(self, url: str, *, timeout_seconds: float) -> FetchOutcome:  # noqa: ARG002
        self.calls.append(url)
        return _outcome(url)


def test_replaying_fetcher_returns_outcome_from_bundle_when_url_present() -> None:
    canned = _outcome()
    fetcher = ReplayingHttpFetcher(
        outcomes_by_url={"https://a.example/1": canned},
    )
    result = fetcher.fetch("https://a.example/1", timeout_seconds=5.0)
    assert result is canned


def test_replaying_fetcher_strict_mode_raises_on_lookup_miss() -> None:
    fetcher = ReplayingHttpFetcher(outcomes_by_url={})
    with pytest.raises(ReplayBundleLookupMissError) as exc:
        fetcher.fetch("https://a.example/missing", timeout_seconds=5.0)
    assert exc.value.category == "fetch_outcome"


def test_replaying_fetcher_permissive_mode_falls_through_to_wrapped() -> None:
    live = _LiveFetcher()
    fetcher = ReplayingHttpFetcher(
        outcomes_by_url={}, wrapped=live, strict=False,
    )
    fetcher.fetch("https://a.example/uncovered", timeout_seconds=5.0)
    assert live.calls == ["https://a.example/uncovered"]


def test_replaying_fetcher_invocation_count_tracks_calls() -> None:
    fetcher = ReplayingHttpFetcher(
        outcomes_by_url={"https://a.example/1": _outcome()},
    )
    fetcher.fetch("https://a.example/1", timeout_seconds=5.0)
    fetcher.fetch("https://a.example/1", timeout_seconds=5.0)
    assert fetcher.invocation_count == 2
