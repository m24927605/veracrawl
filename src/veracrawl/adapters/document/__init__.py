"""Document parsing adapters.

Hosts adapters for non-HTML document handling (PDF text extraction
in Phase 6.3; OCR + table extraction are follow-ups). Core code
depends on the matching :mod:`veracrawl.ports.pdf_text_extractor`
port; concrete parsers live here.
"""
