"""``HybridPdfTextExtractor`` — primary text-layer + OCR fallback.

Composes a primary :class:`PdfTextExtractorPort` (typically
:class:`PypdfTextExtractor`) with an OCR fallback (typically
:class:`PytesseractPdfOcrExtractor`). For each page, returns the
primary extractor's text when it is non-blank; otherwise falls
through to the OCR pipeline so scanned pages get text content.

The composition is one-shot per call:

* Run the primary on the whole PDF (cheap; pypdf is fast).
* If every page has non-blank text, return immediately — no OCR.
* If at least one page is blank, run the OCR extractor on the
  whole PDF (cheaper than per-page rendering twice) and merge
  by page number.

The hybrid is the right default for production crawls because most
PDFs in the wild have text layers; only scanned PDFs pay the OCR
cost.
"""

from __future__ import annotations

from veracrawl.ports.pdf_text_extractor import (
    ExtractedPdfDocument,
    ExtractedPdfPage,
    PdfTextExtractorPort,
)


class HybridPdfTextExtractor:
    """Primary + OCR fallback :class:`PdfTextExtractorPort` impl."""

    def __init__(
        self,
        *,
        primary: PdfTextExtractorPort,
        ocr: PdfTextExtractorPort,
    ) -> None:
        self._primary = primary
        self._ocr = ocr

    def extract(self, body: bytes) -> ExtractedPdfDocument:
        primary_doc = self._primary.extract(body)
        if all(page.text.strip() for page in primary_doc.pages):
            return primary_doc

        ocr_doc = self._ocr.extract(body)
        ocr_by_number = {page.page_number: page.text for page in ocr_doc.pages}

        merged: list[ExtractedPdfPage] = []
        for page in primary_doc.pages:
            if page.text.strip():
                merged.append(page)
            else:
                merged.append(
                    ExtractedPdfPage(
                        page_number=page.page_number,
                        text=ocr_by_number.get(page.page_number, ""),
                    )
                )
        full_text = "\n\n".join(page.text for page in merged)
        return ExtractedPdfDocument(pages=merged, full_text=full_text)


__all__ = ["HybridPdfTextExtractor"]
