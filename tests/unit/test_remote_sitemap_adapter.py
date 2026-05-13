"""Unit tests for :class:`RemoteSitemapAdapter`.

The adapter is fetcher-backed so it has no direct httpx dependency;
tests inject a fake fetcher that returns pre-canned bytes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from veracrawl.external_crawl.remote_sitemap import RemoteSitemapAdapter
from veracrawl.ports.crawl_http_fetcher import FetchOutcome

_VALID_URLSET = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/a</loc></url>
  <url><loc>https://example.com/b</loc></url>
  <url><loc>  https://example.com/c  </loc></url>
</urlset>
"""

_SITEMAPINDEX = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-1.xml</loc></sitemap>
  <sitemap><loc>https://example.com/sitemap-2.xml</loc></sitemap>
</sitemapindex>
"""


@dataclass
class _FakeFetcher:
    pages: dict[str, FetchOutcome]
    calls: list[str] = field(default_factory=list)

    def fetch(self, url: str, *, timeout_seconds: float) -> FetchOutcome:
        self.calls.append(url)
        return self.pages[url]


def _outcome(body: bytes, url: str = "https://example.com/sitemap.xml") -> FetchOutcome:
    return FetchOutcome(
        requested_url=url,
        final_url=url,
        status_code=200,
        headers={"content-type": "application/xml"},
        body=body,
        content_type="application/xml",
    )


def test_parses_urlset_locs() -> None:
    fetcher = _FakeFetcher(pages={"https://example.com/sitemap.xml": _outcome(_VALID_URLSET)})
    adapter = RemoteSitemapAdapter(fetcher=fetcher)
    bundle = adapter.discover("https://example.com/sitemap.xml")
    assert bundle.discovered_urls == [
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    ]
    assert bundle.raw_body == _VALID_URLSET
    assert bundle.source_url == "https://example.com/sitemap.xml"


def test_index_recurses_once() -> None:
    pages = {
        "https://example.com/sitemap.xml": _outcome(_SITEMAPINDEX),
        "https://example.com/sitemap-1.xml": _outcome(_VALID_URLSET, "sm1"),
        "https://example.com/sitemap-2.xml": _outcome(_VALID_URLSET, "sm2"),
    }
    fetcher = _FakeFetcher(pages=pages)
    adapter = RemoteSitemapAdapter(fetcher=fetcher)
    bundle = adapter.discover("https://example.com/sitemap.xml")
    # 3 locs per child x 2 children = 6 entries total (dup tolerated;
    # the frontier dedups).
    assert len(bundle.discovered_urls) == 6
    assert bundle.child_bundles is not None
    assert len(bundle.child_bundles) == 2


def test_malformed_xml_returns_empty_bundle_with_error() -> None:
    fetcher = _FakeFetcher(
        pages={"https://example.com/sitemap.xml": _outcome(b"not xml at all")}
    )
    adapter = RemoteSitemapAdapter(fetcher=fetcher)
    bundle = adapter.discover("https://example.com/sitemap.xml")
    assert bundle.discovered_urls == []
    assert bundle.parse_error is not None


def test_index_recursion_capped_one_level() -> None:
    # A sitemap index whose children are themselves indices should
    # not recurse infinitely — only one level of recursion is
    # followed.
    nested = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/inner.xml</loc></sitemap>
</sitemapindex>
"""
    pages = {
        "https://example.com/sitemap.xml": _outcome(nested),
        "https://example.com/inner.xml": _outcome(nested),
    }
    fetcher = _FakeFetcher(pages=pages)
    adapter = RemoteSitemapAdapter(fetcher=fetcher)
    adapter.discover("https://example.com/sitemap.xml")
    # Top-level fetch + one inner fetch only; the inner index's
    # children must not be followed.
    assert fetcher.calls == [
        "https://example.com/sitemap.xml",
        "https://example.com/inner.xml",
    ]
