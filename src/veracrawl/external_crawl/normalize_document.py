"""Document normalisation for the evidence pipeline.

Produces a :class:`NormalizedDocument` per fetched page with one or
more :class:`NormalizedDocumentAnchor` records. Anchors carry
``(page_number, char_offset_start, char_offset_end, text_hash,
raw_artifact_ref)`` so downstream extraction can cite source spans
without re-parsing the raw bytes.

Supports HTML and plain text out of the box. PDF normalisation
requires a caller-supplied :class:`PdfTextExtractorPort` (Phase 6.3);
absent one, PDFs are flagged ``needs_review`` rather than silently
dropped.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from html.parser import HTMLParser

from veracrawl.ports.pdf_text_extractor import PdfTextExtractorPort


@dataclass(frozen=True, slots=True)
class NormalizedDocumentAnchor:
    page_number: int | None
    char_offset_start: int
    char_offset_end: int
    text_hash: str
    raw_artifact_ref: str


@dataclass(frozen=True, slots=True)
class NormalizedDocument:
    canonical_url: str
    content_type: str
    raw_artifact_ref: str
    text: str
    anchors: list[NormalizedDocumentAnchor]
    status: str  # "ok" | "needs_review"
    reason: str | None = None


class _TextCollector(HTMLParser):
    _SKIP_TAGS = frozenset({"script", "style", "noscript", "template"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self._chunks.append(data)

    def text(self) -> str:
        # Collapse internal whitespace while preserving inter-block
        # spacing — replace runs of whitespace with a single space
        # and strip leading/trailing.
        joined = " ".join("".join(self._chunks).split())
        return joined


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_document(
    *,
    canonical_url: str,
    body: bytes,
    content_type: str,
    raw_artifact_ref: str,
    pdf_extractor: PdfTextExtractorPort | None = None,
) -> NormalizedDocument:
    lowered = (content_type or "").lower()

    if "html" in lowered:
        collector = _TextCollector()
        try:
            collector.feed(body.decode("utf-8", errors="replace"))
        except Exception:  # pragma: no cover - defensive
            return _needs_review(
                canonical_url, content_type, raw_artifact_ref, "html parse failed"
            )
        text = collector.text()
        return _ok(canonical_url, content_type, raw_artifact_ref, text)

    if "plain" in lowered or lowered.startswith("text/") and "html" not in lowered:
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            return _needs_review(
                canonical_url,
                content_type,
                raw_artifact_ref,
                "text body is not valid utf-8",
            )
        return _ok(canonical_url, content_type, raw_artifact_ref, text)

    if "pdf" in lowered:
        if pdf_extractor is None:
            return _needs_review(
                canonical_url,
                content_type,
                raw_artifact_ref,
                "PDF extraction requires a PdfTextExtractorPort; none supplied",
            )
        return _normalize_pdf(
            canonical_url=canonical_url,
            content_type=content_type,
            raw_artifact_ref=raw_artifact_ref,
            body=body,
            extractor=pdf_extractor,
        )

    return _needs_review(
        canonical_url,
        content_type,
        raw_artifact_ref,
        f"no normaliser for content_type {content_type!r}",
    )


def _normalize_pdf(
    *,
    canonical_url: str,
    content_type: str,
    raw_artifact_ref: str,
    body: bytes,
    extractor: PdfTextExtractorPort,
) -> NormalizedDocument:
    try:
        doc = extractor.extract(body)
    except Exception as exc:
        return _needs_review(
            canonical_url,
            content_type,
            raw_artifact_ref,
            f"PDF extraction failed: {exc}",
        )
    if not doc.pages:
        return _needs_review(
            canonical_url,
            content_type,
            raw_artifact_ref,
            "PDF contained zero pages after extraction",
        )

    # Build one anchor per page; offsets are into ``full_text`` so a
    # downstream verifier can pinpoint which page a quoted span came
    # from without re-parsing the PDF.
    anchors: list[NormalizedDocumentAnchor] = []
    cursor = 0
    for page in doc.pages:
        page_text = page.text
        # Pages join with "\n\n"; advance cursor accordingly.
        start = cursor
        end = cursor + len(page_text)
        anchors.append(
            NormalizedDocumentAnchor(
                page_number=page.page_number,
                char_offset_start=start,
                char_offset_end=end,
                text_hash=_hash(page_text),
                raw_artifact_ref=raw_artifact_ref,
            )
        )
        cursor = end + 2  # the "\n\n" separator
    return NormalizedDocument(
        canonical_url=canonical_url,
        content_type=content_type,
        raw_artifact_ref=raw_artifact_ref,
        text=doc.full_text,
        anchors=anchors,
        status="ok",
    )


def _ok(
    canonical_url: str, content_type: str, raw_artifact_ref: str, text: str
) -> NormalizedDocument:
    anchor = NormalizedDocumentAnchor(
        page_number=None,
        char_offset_start=0,
        char_offset_end=len(text),
        text_hash=_hash(text),
        raw_artifact_ref=raw_artifact_ref,
    )
    return NormalizedDocument(
        canonical_url=canonical_url,
        content_type=content_type,
        raw_artifact_ref=raw_artifact_ref,
        text=text,
        anchors=[anchor],
        status="ok",
    )


def _needs_review(
    canonical_url: str, content_type: str, raw_artifact_ref: str, reason: str
) -> NormalizedDocument:
    return NormalizedDocument(
        canonical_url=canonical_url,
        content_type=content_type,
        raw_artifact_ref=raw_artifact_ref,
        text="",
        anchors=field(default_factory=list) if False else [],
        status="needs_review",
        reason=reason,
    )


__all__ = [
    "NormalizedDocument",
    "NormalizedDocumentAnchor",
    "normalize_document",
]
