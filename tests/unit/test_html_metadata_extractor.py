"""Unit tests for :class:`HtmlMetadataExtractor`.

Extracts title, meta description, and h1 from HTML, returning
:class:`ExtractionCandidate` records that cite the document's
single full-body anchor.
"""

from __future__ import annotations

from veracrawl.external_crawl.html_metadata_extractor import HtmlMetadataExtractor
from veracrawl.external_crawl.normalize_document import (
    NormalizedDocumentAnchor,
    normalize_document,
)
from veracrawl.ports.extractor import ExtractionRequest

_ANCHOR = NormalizedDocumentAnchor(
    page_number=None,
    char_offset_start=0,
    char_offset_end=999,
    text_hash="b" * 64,
    raw_artifact_ref="raw-html/abc",
)


def _request(body: bytes, url: str = "https://example.com/") -> ExtractionRequest:
    normalized = normalize_document(
        canonical_url=url,
        body=body,
        content_type="text/html",
        raw_artifact_ref="raw-html/abc",
    )
    return ExtractionRequest(
        canonical_url=url,
        normalized_text=normalized.text,
        raw_body=body,
        content_type="text/html",
        raw_artifact_ref="raw-html/abc",
        anchors=normalized.anchors,
    )


def test_extracts_title_meta_description_and_h1() -> None:
    body = b"""<html><head>
        <title>Example Page</title>
        <meta name="description" content="An example description.">
    </head><body>
        <h1>Heading One</h1>
        <p>Body copy.</p>
    </body></html>"""

    result = HtmlMetadataExtractor().extract(_request(body))

    assert result.status == "ok"
    assert len(result.candidates) == 1
    fields = result.candidates[0].fields
    assert fields["title"] == "Example Page"
    assert fields["meta_description"] == "An example description."
    assert fields["h1"] == "Heading One"


def test_anchors_propagated_into_candidate() -> None:
    body = b"<html><head><title>Anchored</title></head><body><h1>Hi</h1></body></html>"
    result = HtmlMetadataExtractor().extract(_request(body))
    anchors = result.candidates[0].evidence_anchors
    assert len(anchors) >= 1
    assert anchors[0].text_hash  # populated


def test_non_html_returns_needs_review() -> None:
    pdf_request = ExtractionRequest(
        canonical_url="https://example.com/x.pdf",
        normalized_text="",
        raw_body=b"%PDF-1.4 ...",
        content_type="application/pdf",
        raw_artifact_ref="documents/abc.pdf",
        anchors=[_ANCHOR],
    )
    result = HtmlMetadataExtractor().extract(pdf_request)
    assert result.status == "needs_review"
    assert result.candidates == []


def test_extractor_emits_no_candidate_when_no_fields_found() -> None:
    # An empty page produces nothing; the extractor must NOT
    # fabricate a candidate with stub values.
    body = b"<html><body></body></html>"
    result = HtmlMetadataExtractor().extract(_request(body))
    assert result.candidates == []
    assert result.status in {"ok", "needs_review"}
