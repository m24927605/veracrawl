"""OCR adapter + hybrid PDF extractor tests.

We generate an image-only PDF on the fly so the test stays hermetic.
PIL/Pillow renders text into a PNG and saves the image directly as
a PDF — the resulting file has no text layer, so a pure pypdf
extraction returns empty page text and the OCR fallback fires.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw, ImageFont

from veracrawl.adapters.document.hybrid_pdf_text_extractor import (
    HybridPdfTextExtractor,
)
from veracrawl.adapters.document.pypdf_text_extractor import PypdfTextExtractor
from veracrawl.adapters.document.pytesseract_pdf_ocr_extractor import (
    PdfOcrError,
    PytesseractPdfOcrExtractor,
)
from veracrawl.external_crawl.normalize_document import normalize_document


def _scanned_pdf_bytes(message: str = "Hello OCR World") -> bytes:
    """Build a one-page image-only PDF containing rendered text."""
    image = Image.new("RGB", (1200, 400), "white")
    draw = ImageDraw.Draw(image)
    # Pillow's default font is bitmapped and small; OCR accuracy on
    # the default font is unreliable. Try to load a TrueType font;
    # fall back to default if not available.
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    try:
        font = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Arial.ttf", size=96
        )
    except OSError:
        font = ImageFont.load_default()
    draw.text((60, 120), message, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PDF")
    return buffer.getvalue()


def test_pure_ocr_extractor_recovers_text_from_scanned_pdf() -> None:
    pdf = _scanned_pdf_bytes("Hello OCR World")
    extractor = PytesseractPdfOcrExtractor()
    doc = extractor.extract(pdf)
    assert len(doc.pages) == 1
    # OCR is approximate; require the recognisable substring.
    assert "Hello" in doc.pages[0].text
    assert "OCR" in doc.pages[0].text


def test_hybrid_falls_back_to_ocr_for_image_only_pdf() -> None:
    pdf = _scanned_pdf_bytes("Hybrid Path Hello")
    hybrid = HybridPdfTextExtractor(
        primary=PypdfTextExtractor(),
        ocr=PytesseractPdfOcrExtractor(),
    )
    doc = hybrid.extract(pdf)
    assert len(doc.pages) == 1
    assert "Hybrid" in doc.pages[0].text
    assert "Hello" in doc.pages[0].text


def test_hybrid_skips_ocr_when_primary_has_text() -> None:
    # Build a fake primary that returns rich text for every page.
    from dataclasses import dataclass

    from veracrawl.ports.pdf_text_extractor import (
        ExtractedPdfDocument,
        ExtractedPdfPage,
    )

    @dataclass
    class _RichPrimary:
        def extract(self, body: bytes) -> ExtractedPdfDocument:
            page = ExtractedPdfPage(page_number=1, text="rich primary text")
            return ExtractedPdfDocument(pages=[page], full_text=page.text)

    class _OcrShouldNotRun:
        def extract(self, body: bytes) -> ExtractedPdfDocument:  # pragma: no cover
            raise AssertionError("OCR must not be invoked when primary has text")

    hybrid = HybridPdfTextExtractor(primary=_RichPrimary(), ocr=_OcrShouldNotRun())
    doc = hybrid.extract(b"%PDF-1.4 ...")
    assert doc.pages[0].text == "rich primary text"


def test_normalize_document_with_hybrid_extractor_marks_scanned_pdf_ok() -> None:
    pdf = _scanned_pdf_bytes("Normalisation Hello")
    hybrid = HybridPdfTextExtractor(
        primary=PypdfTextExtractor(),
        ocr=PytesseractPdfOcrExtractor(),
    )
    result = normalize_document(
        canonical_url="https://example.com/scanned.pdf",
        body=pdf,
        content_type="application/pdf",
        raw_artifact_ref="documents/scanned.pdf",
        pdf_extractor=hybrid,
    )
    assert result.status == "ok"
    assert "Normalisation" in result.text or "Hello" in result.text
    assert len(result.anchors) == 1


def test_ocr_extractor_refuses_invalid_pdf() -> None:
    extractor = PytesseractPdfOcrExtractor()
    with pytest.raises(PdfOcrError):
        extractor.extract(b"not a pdf")
