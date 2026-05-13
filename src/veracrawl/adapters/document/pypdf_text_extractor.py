"""``PypdfTextExtractor`` — Phase 6.3 :class:`PdfTextExtractorPort` impl.

Built on :mod:`pypdf`. Returns one :class:`ExtractedPdfPage` per
visible page and the joined full-text string for downstream anchor
construction.

Failure modes:

* Encrypted PDFs without a password → raises :class:`PdfTextExtractionError`;
  callers (the document normaliser) downgrade to ``needs_review``.
* Empty PDFs (zero pages) → returns an empty document; the
  normaliser then has no anchors and reports ``needs_review``.
* Pages that contain only scanned imagery (no text layer) → emit
  empty page text; the normaliser still records the page-level
  anchor so a downstream OCR pass can fill it in.
"""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from veracrawl.ports.pdf_text_extractor import (
    ExtractedPdfDocument,
    ExtractedPdfPage,
)


class PdfTextExtractionError(RuntimeError):
    """Raised when pypdf refuses or fails to parse a PDF."""


class PypdfTextExtractor:
    """Default :class:`PdfTextExtractorPort` impl backed by :mod:`pypdf`."""

    def extract(self, body: bytes) -> ExtractedPdfDocument:
        try:
            reader = PdfReader(BytesIO(body))
        except (PdfReadError, OSError, ValueError) as exc:
            raise PdfTextExtractionError(f"pypdf could not parse the PDF: {exc}") from exc

        if reader.is_encrypted:
            raise PdfTextExtractionError(
                "PDF is encrypted; PypdfTextExtractor does not support password-protected files"
            )

        pages: list[ExtractedPdfPage] = []
        for index, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # pragma: no cover - defensive
                raise PdfTextExtractionError(
                    f"failed extracting text from page {index}: {exc}"
                ) from exc
            pages.append(ExtractedPdfPage(page_number=index, text=text))

        full_text = "\n\n".join(page.text for page in pages)
        return ExtractedPdfDocument(pages=pages, full_text=full_text)


__all__ = ["PdfTextExtractionError", "PypdfTextExtractor"]
