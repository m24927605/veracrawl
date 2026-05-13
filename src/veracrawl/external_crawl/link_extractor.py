"""Stdlib-only ``<a href="...">`` extractor for the Phase 2 crawl loop.

We avoid pulling in ``lxml``/``beautifulsoup4`` for Phase 2 — the
goal is "discover links, persist evidence", not "parse arbitrary
HTML perfectly". The extractor is intentionally lossy: it only
follows ``<a href>``, skips ``<link>``/``<area>``/``<form>``, and
ignores ``javascript:``/``mailto:`` schemes. Callers that need a
richer link graph can swap a different extractor behind the
:class:`LinkExtractor` interface.
"""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import urljoin


class LinkExtractor(Protocol):
    def extract(self, *, base_url: str, body: bytes, content_type: str) -> list[str]: ...


class _AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)
                return


class HtmlAnchorExtractor:
    """Extract absolute URLs from ``<a href>`` tags in an HTML document.

    Resolves relative hrefs against ``base_url`` so callers can
    canonicalise the result without re-doing the join.
    """

    def extract(self, *, base_url: str, body: bytes, content_type: str) -> list[str]:
        if "html" not in (content_type or "").lower():
            return []
        text = body.decode("utf-8", errors="replace")
        collector = _AnchorCollector()
        try:
            collector.feed(text)
        except Exception:  # pragma: no cover - defensive
            return []
        absolute: list[str] = []
        for href in collector.hrefs:
            href = href.strip()
            if not href:
                continue
            lowered = href.lower()
            if lowered.startswith(("javascript:", "mailto:", "tel:", "data:")):
                continue
            absolute.append(urljoin(base_url, href))
        return absolute


__all__ = ["HtmlAnchorExtractor", "LinkExtractor"]
