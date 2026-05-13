"""Deterministic HTML metadata extractor.

Phase 4.2's first :class:`ExtractorPort` impl. Pulls title,
meta description, and first ``<h1>`` from HTML via stdlib
:mod:`html.parser`. No external deps.

Every extracted candidate cites the request's full-body anchor; the
extractor never fabricates evidence — empty pages produce zero
candidates with ``status="ok"``.
"""

from __future__ import annotations

from html.parser import HTMLParser

from veracrawl.ports.extractor import (
    ExtractionCandidate,
    ExtractionRequest,
    ExtractionResult,
)

_SCHEMA_REF = "schema:external-crawl/html-metadata/v1"


class _MetadataCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self.meta_description: str | None = None
        self.h1: str | None = None
        self._in_title = False
        self._in_h1 = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = True
        elif tag == "h1" and self.h1 is None:
            self._in_h1 = True
        elif tag == "meta":
            name = None
            content = None
            for key, value in attrs:
                lkey = key.lower()
                if lkey == "name":
                    name = (value or "").lower()
                elif lkey == "content":
                    content = value
            if name == "description" and content and self.meta_description is None:
                self.meta_description = content.strip() or None

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        if self._in_title and self.title is None:
            stripped = data.strip()
            if stripped:
                self.title = stripped
        if self._in_h1 and self.h1 is None:
            stripped = data.strip()
            if stripped:
                self.h1 = stripped


class HtmlMetadataExtractor:
    """Phase 4.2 :class:`ExtractorPort` impl for HTML metadata."""

    schema_ref: str = _SCHEMA_REF

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        if "html" not in (request.content_type or "").lower():
            return ExtractionResult(
                canonical_url=request.canonical_url,
                candidates=[],
                status="needs_review",
                reason=(
                    f"content_type {request.content_type!r} not supported "
                    "by HtmlMetadataExtractor"
                ),
            )

        if not request.anchors:
            return ExtractionResult(
                canonical_url=request.canonical_url,
                candidates=[],
                status="needs_review",
                reason="request carries no anchors; cannot cite evidence",
            )

        # Title and meta tags don't survive normalisation, so parse
        # the raw HTML directly. Anchors still cite the normalised
        # text hash for verifier replay.
        collector = _MetadataCollector()
        try:
            collector.feed(request.raw_body.decode("utf-8", errors="replace"))
        except Exception:  # pragma: no cover - defensive
            return ExtractionResult(
                canonical_url=request.canonical_url,
                candidates=[],
                status="needs_review",
                reason="HTML parse failed",
            )

        fields: dict[str, object] = {}
        if collector.title:
            fields["title"] = collector.title
        if collector.meta_description:
            fields["meta_description"] = collector.meta_description
        if collector.h1:
            fields["h1"] = collector.h1

        if not fields:
            return ExtractionResult(
                canonical_url=request.canonical_url,
                candidates=[],
                status="ok",
                reason="no metadata fields present in document",
            )

        candidate = ExtractionCandidate(
            canonical_url=request.canonical_url,
            schema_ref=self.schema_ref,
            fields=fields,
            evidence_anchors=list(request.anchors),
        )
        return ExtractionResult(
            canonical_url=request.canonical_url,
            candidates=[candidate],
            status="ok",
        )


__all__ = ["HtmlMetadataExtractor"]
