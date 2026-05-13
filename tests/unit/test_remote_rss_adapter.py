"""Unit tests for :class:`RemoteRssAdapter`.

Covers RSS 2.0 and Atom 1.0 link extraction. Uses a fake fetcher
so no network I/O occurs.
"""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.external_crawl.remote_rss import RemoteRssAdapter
from veracrawl.ports.crawl_http_fetcher import FetchOutcome

_RSS_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>VeraCrawl Test Feed</title>
    <link>https://example.com/</link>
    <item>
      <title>Post A</title>
      <link>https://example.com/post-a</link>
    </item>
    <item>
      <title>Post B</title>
      <link>https://example.com/post-b</link>
    </item>
  </channel>
</rss>
"""

_ATOM_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>VeraCrawl Test Atom</title>
  <link href="https://example.com/"/>
  <entry>
    <title>Entry 1</title>
    <link href="https://example.com/entry-1"/>
  </entry>
  <entry>
    <title>Entry 2</title>
    <link href="https://example.com/entry-2" rel="alternate"/>
  </entry>
</feed>
"""


@dataclass
class _FakeFetcher:
    body: bytes

    def fetch(self, url: str, *, timeout_seconds: float) -> FetchOutcome:
        return FetchOutcome(
            requested_url=url,
            final_url=url,
            status_code=200,
            headers={"content-type": "application/xml"},
            body=self.body,
            content_type="application/xml",
        )


def test_extracts_item_links_from_rss_20() -> None:
    adapter = RemoteRssAdapter(fetcher=_FakeFetcher(body=_RSS_FEED))
    bundle = adapter.discover("https://example.com/feed.xml")
    assert bundle.discovered_urls == [
        "https://example.com/post-a",
        "https://example.com/post-b",
    ]


def test_extracts_entry_links_from_atom() -> None:
    adapter = RemoteRssAdapter(fetcher=_FakeFetcher(body=_ATOM_FEED))
    bundle = adapter.discover("https://example.com/atom.xml")
    assert bundle.discovered_urls == [
        "https://example.com/entry-1",
        "https://example.com/entry-2",
    ]


def test_malformed_feed_returns_empty_with_error() -> None:
    adapter = RemoteRssAdapter(fetcher=_FakeFetcher(body=b"not xml"))
    bundle = adapter.discover("https://example.com/broken.xml")
    assert bundle.discovered_urls == []
    assert bundle.parse_error is not None


def test_non_feed_xml_returns_empty() -> None:
    # A urlset sitemap is XML but not a feed; the adapter should
    # decline rather than misinterpret it.
    sitemap = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/x</loc></url>
</urlset>"""
    adapter = RemoteRssAdapter(fetcher=_FakeFetcher(body=sitemap))
    bundle = adapter.discover("https://example.com/not-a-feed.xml")
    assert bundle.discovered_urls == []
