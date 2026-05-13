"""Remote RSS/Atom feed adapter.

Fetches a feed via :class:`CrawlHttpFetcherPort` and extracts entry
links. Supports RSS 2.0 (``<rss><channel><item><link>``) and Atom
1.0 (``<feed><entry><link href>``). Pure stdlib XML parsing — no
external deps. Returns a :class:`FeedDiscoveryBundle` carrying the
raw bytes so the runner can persist the artifact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from xml.etree.ElementTree import Element, ParseError, fromstring

from veracrawl.ports.crawl_http_fetcher import (
    CrawlHttpFetcherPort,
    FetchError,
    FetchOutcome,
)

_ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}


@dataclass(frozen=True, slots=True)
class FeedDiscoveryBundle:
    source_url: str
    raw_body: bytes
    content_type: str
    discovered_urls: list[str] = field(default_factory=list)
    feed_kind: str | None = None  # "rss" | "atom" | None
    parse_error: str | None = None


def _parse_feed(body: bytes) -> tuple[list[str], str | None, str | None]:
    """Return ``(urls, feed_kind, error_message)``."""
    try:
        root = fromstring(body)
    except ParseError as exc:
        return [], None, str(exc)

    tag = root.tag.split("}", 1)[-1] if "}" in root.tag else root.tag

    if tag == "rss":
        channel = root.find("channel")
        if channel is None:
            return [], "rss", "rss root has no <channel>"
        urls: list[str] = []
        for item in channel.findall("item"):
            link = item.find("link")
            if link is not None and link.text:
                stripped = link.text.strip()
                if stripped:
                    urls.append(stripped)
        return urls, "rss", None

    if tag == "feed":
        atom_urls: list[str] = []
        for entry in root.findall("a:entry", _ATOM_NS) or root.findall("entry"):
            href = _first_alternate_link(entry)
            if href is not None:
                atom_urls.append(href)
        return atom_urls, "atom", None

    return [], None, f"unrecognised feed root element: {tag!r}"


def _first_alternate_link(entry: Element) -> str | None:
    candidates = entry.findall("a:link", _ATOM_NS) or entry.findall("link")
    for link in candidates:
        rel = link.attrib.get("rel", "alternate")
        href = link.attrib.get("href")
        if href and rel in ("", "alternate"):
            return href.strip() or None
    return None


@dataclass(slots=True)
class RemoteRssAdapter:
    fetcher: CrawlHttpFetcherPort
    timeout_seconds: float = 10.0

    def discover(self, feed_url: str) -> FeedDiscoveryBundle:
        try:
            outcome: FetchOutcome = self.fetcher.fetch(
                feed_url, timeout_seconds=self.timeout_seconds
            )
        except FetchError as exc:
            return FeedDiscoveryBundle(
                source_url=feed_url,
                raw_body=b"",
                content_type="",
                parse_error=f"fetch failed: {exc}",
            )

        urls, feed_kind, error = _parse_feed(outcome.body)
        return FeedDiscoveryBundle(
            source_url=feed_url,
            raw_body=outcome.body,
            content_type=outcome.content_type,
            discovered_urls=urls,
            feed_kind=feed_kind,
            parse_error=error,
        )


__all__ = ["FeedDiscoveryBundle", "RemoteRssAdapter"]
