"""Remote sitemap adapter.

Fetches a ``sitemap.xml`` (or sitemap index) via
:class:`CrawlHttpFetcherPort`, parses ``<loc>`` entries, and returns
a :class:`SitemapDiscoveryBundle` carrying the discovered URLs and
the raw response bytes (so the runner can persist the artifact).

The adapter is deliberately conservative:

* It uses :mod:`xml.etree.ElementTree` (stdlib, no external deps).
* It recurses *one* level into sitemap indices and refuses to follow
  any deeper nesting — operators with truly nested sitemaps can
  re-seed manually.
* It treats parser failures as soft errors (returns an empty
  bundle with ``parse_error`` set) so a single malformed file does
  not crash the runner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from xml.etree.ElementTree import ParseError, fromstring

from veracrawl.ports.crawl_http_fetcher import (
    CrawlHttpFetcherPort,
    FetchError,
    FetchOutcome,
)

_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass(frozen=True, slots=True)
class SitemapDiscoveryBundle:
    source_url: str
    raw_body: bytes
    content_type: str
    discovered_urls: list[str] = field(default_factory=list)
    child_bundles: list[SitemapDiscoveryBundle] | None = None
    parse_error: str | None = None


def _parse_locs(body: bytes) -> tuple[list[str], list[str], str | None]:
    """Return ``(urls, child_sitemap_urls, error_message)``."""
    try:
        root = fromstring(body)
    except ParseError as exc:
        return [], [], str(exc)

    tag = root.tag.split("}", 1)[-1] if "}" in root.tag else root.tag
    urls: list[str] = []
    children: list[str] = []
    if tag == "urlset":
        for url_elem in root.findall("sm:url", _NS) or root.findall("url"):
            loc = _loc_text(url_elem)
            if loc:
                urls.append(loc)
    elif tag == "sitemapindex":
        for sm in root.findall("sm:sitemap", _NS) or root.findall("sitemap"):
            loc = _loc_text(sm)
            if loc:
                children.append(loc)
    else:
        return [], [], f"unexpected root element: {tag!r}"
    return urls, children, None


def _loc_text(element: object) -> str | None:
    # ``element`` is an ElementTree Element; using object typing
    # keeps the public type annotations free of ET internals.
    from xml.etree.ElementTree import Element

    assert isinstance(element, Element)
    loc = element.find("sm:loc", _NS)
    if loc is None:
        loc = element.find("loc")
    if loc is None or loc.text is None:
        return None
    return loc.text.strip() or None


@dataclass(slots=True)
class RemoteSitemapAdapter:
    fetcher: CrawlHttpFetcherPort
    timeout_seconds: float = 10.0

    def discover(
        self, sitemap_url: str, *, _recursion_depth: int = 0
    ) -> SitemapDiscoveryBundle:
        try:
            outcome: FetchOutcome = self.fetcher.fetch(
                sitemap_url, timeout_seconds=self.timeout_seconds
            )
        except FetchError as exc:
            return SitemapDiscoveryBundle(
                source_url=sitemap_url,
                raw_body=b"",
                content_type="",
                parse_error=f"fetch failed: {exc}",
            )

        urls, child_urls, error = _parse_locs(outcome.body)
        child_bundles: list[SitemapDiscoveryBundle] | None = None
        if child_urls and _recursion_depth == 0:
            child_bundles = []
            for child in child_urls:
                child_bundle = self.discover(child, _recursion_depth=1)
                child_bundles.append(child_bundle)
                urls.extend(child_bundle.discovered_urls)
        return SitemapDiscoveryBundle(
            source_url=sitemap_url,
            raw_body=outcome.body,
            content_type=outcome.content_type,
            discovered_urls=urls,
            child_bundles=child_bundles,
            parse_error=error,
        )


__all__ = ["RemoteSitemapAdapter", "SitemapDiscoveryBundle"]
