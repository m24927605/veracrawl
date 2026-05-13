"""Contract tests for the external-crawl extraction surface.

Defines the boundary every Phase 4 extractor must honour:
* every extracted field must reference at least one evidence anchor;
* a candidate with empty anchors fails validation;
* anchors are dataclass-equal (so dedup works).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.external_crawl.normalize_document import NormalizedDocumentAnchor
from veracrawl.ports.extractor import (
    ExtractionCandidate,
    ExtractionRequest,
    ExtractionResult,
    ExtractorPort,
)


def _anchor() -> NormalizedDocumentAnchor:
    return NormalizedDocumentAnchor(
        page_number=None,
        char_offset_start=0,
        char_offset_end=10,
        text_hash="a" * 64,
        raw_artifact_ref="raw-html/abc",
    )


def test_candidate_requires_at_least_one_evidence_anchor() -> None:
    with pytest.raises(ValidationError, match="evidence_anchors"):
        ExtractionCandidate(
            canonical_url="https://example.com/",
            schema_ref="schema:demo",
            fields={"title": "x"},
            evidence_anchors=[],
        )


def test_candidate_requires_non_empty_fields() -> None:
    with pytest.raises(ValidationError, match="fields"):
        ExtractionCandidate(
            canonical_url="https://example.com/",
            schema_ref="schema:demo",
            fields={},
            evidence_anchors=[_anchor()],
        )


def test_candidate_valid_minimal_shape() -> None:
    candidate = ExtractionCandidate(
        canonical_url="https://example.com/",
        schema_ref="schema:demo",
        fields={"title": "x"},
        evidence_anchors=[_anchor()],
    )
    assert candidate.evidence_anchors[0].text_hash == "a" * 64


def test_extraction_result_aggregates_candidates() -> None:
    result = ExtractionResult(
        canonical_url="https://example.com/",
        candidates=[
            ExtractionCandidate(
                canonical_url="https://example.com/",
                schema_ref="schema:demo",
                fields={"title": "x"},
                evidence_anchors=[_anchor()],
            )
        ],
        status="ok",
    )
    assert result.status == "ok"
    assert len(result.candidates) == 1


def test_extraction_result_needs_review_status_allows_empty_candidates() -> None:
    # When the extractor can't satisfy the schema (e.g., binary PDF),
    # it returns ``status="needs_review"`` rather than fabricating
    # evidence-less candidates.
    result = ExtractionResult(
        canonical_url="https://example.com/x.pdf",
        candidates=[],
        status="needs_review",
        reason="content type not supported",
    )
    assert result.status == "needs_review"


def test_protocol_check_minimal_implementation() -> None:
    class _Extractor:
        def extract(self, request: ExtractionRequest) -> ExtractionResult:
            return ExtractionResult(
                canonical_url=request.canonical_url,
                candidates=[],
                status="ok",
            )

    extractor: ExtractorPort = _Extractor()
    out = extractor.extract(
        ExtractionRequest(
            canonical_url="https://example.com/",
            normalized_text="hi",
            raw_body=b"hi",
            content_type="text/html",
            raw_artifact_ref="raw-html/abc",
            anchors=[_anchor()],
        )
    )
    assert isinstance(out, ExtractionResult)
