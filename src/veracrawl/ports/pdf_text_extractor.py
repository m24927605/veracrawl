"""``PdfTextExtractorPort`` — narrow PDF text extraction surface.

Used by the document normaliser to extract per-page text from PDF
artifacts. The port returns one :class:`ExtractedPdfPage` per page
plus the joined document text so the normaliser can build anchors
without knowing the underlying parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ExtractedPdfPage:
    page_number: int  # 1-indexed
    text: str


@dataclass(frozen=True, slots=True)
class ExtractedPdfDocument:
    pages: list[ExtractedPdfPage]
    full_text: str  # pages joined by "\n\n"


class PdfTextExtractorPort(Protocol):
    def extract(self, body: bytes) -> ExtractedPdfDocument: ...


__all__ = [
    "ExtractedPdfDocument",
    "ExtractedPdfPage",
    "PdfTextExtractorPort",
]
