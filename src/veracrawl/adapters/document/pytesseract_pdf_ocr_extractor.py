"""``PytesseractPdfOcrExtractor`` — OCR-only :class:`PdfTextExtractorPort` impl.

Renders each PDF page to an image via :mod:`pdf2image` (Poppler) and
sends it to :mod:`pytesseract` for recognition. Returns one page of
OCR text per PDF page.

Use this when you know the PDF is image-only (a scan with no text
layer). For PDFs that mix real text + scans, see
:class:`HybridPdfTextExtractor` which only falls back to OCR for
pages where the text-layer extractor returned empty.

Requires the system-level ``tesseract`` and ``poppler`` binaries plus
the ``pdf-ocr`` Python extra.
"""

from __future__ import annotations

import pdf2image
import pytesseract

from veracrawl.ports.pdf_text_extractor import (
    ExtractedPdfDocument,
    ExtractedPdfPage,
)


class PdfOcrError(RuntimeError):
    """Raised when the OCR pipeline fails to produce a result."""


class PytesseractPdfOcrExtractor:
    """OCR-backed :class:`PdfTextExtractorPort` implementation."""

    def __init__(
        self,
        *,
        language: str = "eng",
        dpi: int = 200,
        timeout_seconds: int = 30,
    ) -> None:
        if not language or not language.strip():
            raise ValueError("language must be non-empty")
        if dpi <= 0:
            raise ValueError("dpi must be positive")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._language = language
        self._dpi = dpi
        self._timeout = timeout_seconds

    def extract(self, body: bytes) -> ExtractedPdfDocument:
        try:
            images = pdf2image.convert_from_bytes(body, dpi=self._dpi)
        except Exception as exc:
            raise PdfOcrError(f"pdf2image failed to render PDF: {exc}") from exc

        pages: list[ExtractedPdfPage] = []
        for index, image in enumerate(images, start=1):
            try:
                text = pytesseract.image_to_string(
                    image, lang=self._language, timeout=self._timeout
                )
            except Exception as exc:
                raise PdfOcrError(
                    f"pytesseract failed on page {index}: {exc}"
                ) from exc
            pages.append(ExtractedPdfPage(page_number=index, text=text))

        full_text = "\n\n".join(page.text for page in pages)
        return ExtractedPdfDocument(pages=pages, full_text=full_text)


__all__ = ["PdfOcrError", "PytesseractPdfOcrExtractor"]
