"""Unit tests for PDF text extraction + PDF document normalisation."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter

from veracrawl.adapters.document.pypdf_text_extractor import (
    PdfTextExtractionError,
    PypdfTextExtractor,
)
from veracrawl.external_crawl.normalize_document import normalize_document
from veracrawl.ports.pdf_text_extractor import (
    ExtractedPdfDocument,
    ExtractedPdfPage,
)


@dataclass
class _StubExtractor:
    document: ExtractedPdfDocument

    def extract(self, body: bytes) -> ExtractedPdfDocument:
        return self.document


def _two_page_pdf_bytes() -> bytes:
    # Construct a minimal two-page PDF in-process using pypdf so the
    # test stays hermetic and doesn't require a binary fixture.
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_pypdf_extractor_returns_one_page_per_pdf_page() -> None:
    extractor = PypdfTextExtractor()
    doc = extractor.extract(_two_page_pdf_bytes())
    assert len(doc.pages) == 2
    assert [p.page_number for p in doc.pages] == [1, 2]


def test_pypdf_extractor_refuses_malformed_pdf() -> None:
    extractor = PypdfTextExtractor()
    with pytest.raises(PdfTextExtractionError):
        extractor.extract(b"not a pdf")


def test_normalize_pdf_without_extractor_returns_needs_review() -> None:
    result = normalize_document(
        canonical_url="https://example.com/x.pdf",
        body=b"%PDF-1.4",
        content_type="application/pdf",
        raw_artifact_ref="documents/x.pdf",
    )
    assert result.status == "needs_review"
    assert result.reason and "PdfTextExtractorPort" in result.reason


def test_normalize_pdf_with_extractor_produces_per_page_anchors() -> None:
    fake_doc = ExtractedPdfDocument(
        pages=[
            ExtractedPdfPage(page_number=1, text="Hello page one."),
            ExtractedPdfPage(page_number=2, text="Page two content here."),
        ],
        full_text="Hello page one.\n\nPage two content here.",
    )
    result = normalize_document(
        canonical_url="https://example.com/x.pdf",
        body=b"%PDF-1.4",
        content_type="application/pdf",
        raw_artifact_ref="documents/x.pdf",
        pdf_extractor=_StubExtractor(document=fake_doc),
    )
    assert result.status == "ok"
    assert result.text == "Hello page one.\n\nPage two content here."
    assert len(result.anchors) == 2
    assert result.anchors[0].page_number == 1
    assert result.anchors[1].page_number == 2
    # Anchor offsets must cover their page text exactly.
    page_one_text = result.text[
        result.anchors[0].char_offset_start : result.anchors[0].char_offset_end
    ]
    assert page_one_text == "Hello page one."


def test_normalize_pdf_with_zero_pages_returns_needs_review() -> None:
    empty_doc = ExtractedPdfDocument(pages=[], full_text="")
    result = normalize_document(
        canonical_url="https://example.com/x.pdf",
        body=b"%PDF-1.4",
        content_type="application/pdf",
        raw_artifact_ref="documents/x.pdf",
        pdf_extractor=_StubExtractor(document=empty_doc),
    )
    assert result.status == "needs_review"


def test_normalize_pdf_extractor_failure_returns_needs_review() -> None:
    class _Boom:
        def extract(self, body: bytes) -> ExtractedPdfDocument:
            raise RuntimeError("kaboom")

    result = normalize_document(
        canonical_url="https://example.com/x.pdf",
        body=b"%PDF-1.4",
        content_type="application/pdf",
        raw_artifact_ref="documents/x.pdf",
        pdf_extractor=_Boom(),
    )
    assert result.status == "needs_review"
    assert "kaboom" in (result.reason or "")


def test_round_trip_pypdf_through_normalize_document() -> None:
    # Real pypdf round-trip: PDF created by PdfWriter has no text,
    # but the normaliser should still report anchors per page (with
    # empty page text, which a future OCR pass would fill in).
    body = _two_page_pdf_bytes()
    assert PdfReader(BytesIO(body)).pages, "fixture sanity check"
    result = normalize_document(
        canonical_url="https://example.com/blank.pdf",
        body=body,
        content_type="application/pdf",
        raw_artifact_ref="documents/blank.pdf",
        pdf_extractor=PypdfTextExtractor(),
    )
    assert result.status == "ok"
    assert len(result.anchors) == 2
    assert [a.page_number for a in result.anchors] == [1, 2]
