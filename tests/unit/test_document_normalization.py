"""Unit tests for the Phase 3.4 document normalisation helpers.

The runner uses these helpers to produce one ``NormalizedDocument``
per fetched page, including per-anchor offsets that callers can use
to reconstruct evidence spans without re-parsing the raw artifact.
"""

from __future__ import annotations

import hashlib

from veracrawl.external_crawl.normalize_document import (
    NormalizedDocument,
    NormalizedDocumentAnchor,
    normalize_document,
)


def test_html_document_strips_tags_and_records_full_span_anchor() -> None:
    body = (
        b"<html><body><h1>Title</h1><p>Hello world.</p>"
        b"<script>ignored</script></body></html>"
    )
    normalized: NormalizedDocument = normalize_document(
        canonical_url="https://example.com/p",
        body=body,
        content_type="text/html",
        raw_artifact_ref="raw-html/abc",
    )
    assert normalized.status == "ok"
    # Text must collapse runs of whitespace but preserve order.
    assert "Title" in normalized.text
    assert "Hello world." in normalized.text
    assert "ignored" not in normalized.text  # script content stripped
    assert len(normalized.anchors) == 1
    anchor = normalized.anchors[0]
    assert anchor.char_offset_start == 0
    assert anchor.char_offset_end == len(normalized.text)
    assert anchor.page_number is None
    assert anchor.raw_artifact_ref == "raw-html/abc"
    assert anchor.text_hash == hashlib.sha256(normalized.text.encode("utf-8")).hexdigest()


def test_plain_text_document_preserves_text_and_records_anchor() -> None:
    text = "Hello world.\nLine two."
    normalized = normalize_document(
        canonical_url="https://example.com/notes.txt",
        body=text.encode("utf-8"),
        content_type="text/plain",
        raw_artifact_ref="documents/abc.txt",
    )
    assert normalized.status == "ok"
    assert normalized.text == text
    assert len(normalized.anchors) == 1
    assert normalized.anchors[0].text_hash == hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def test_pdf_document_marked_needs_review() -> None:
    normalized = normalize_document(
        canonical_url="https://example.com/file.pdf",
        body=b"%PDF-1.4 ...",
        content_type="application/pdf",
        raw_artifact_ref="documents/abc.pdf",
    )
    assert normalized.status == "needs_review"
    assert normalized.reason and "pdf" in normalized.reason.lower()
    assert normalized.text == ""
    assert normalized.anchors == []


def test_unknown_binary_document_marked_needs_review() -> None:
    normalized = normalize_document(
        canonical_url="https://example.com/x",
        body=b"\x00\x01\x02",
        content_type="application/octet-stream",
        raw_artifact_ref="documents/abc.bin",
    )
    assert normalized.status == "needs_review"
    assert normalized.anchors == []


def test_normalized_document_anchor_is_hashable_for_dedup() -> None:
    anchor = NormalizedDocumentAnchor(
        page_number=None,
        char_offset_start=0,
        char_offset_end=5,
        text_hash="a" * 64,
        raw_artifact_ref="raw-html/a",
    )
    # Two equal anchors should be equal.
    same = NormalizedDocumentAnchor(
        page_number=None,
        char_offset_start=0,
        char_offset_end=5,
        text_hash="a" * 64,
        raw_artifact_ref="raw-html/a",
    )
    assert anchor == same
