"""Unit tests for :class:`LlmAssistedExtractor` and its trace recorder.

The adapter sits behind ``LlmExtractCallable`` so the test does not
require a real LLM. A stub callable returns canned field+quote
pairs; the adapter is responsible for anchor-matching each quote
against the normalised text and refusing candidates whose quotes
don't match.
"""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.adapters.model_providers.llm_assisted_extractor import (
    LlmAssistedExtractor,
    LlmExtractResponse,
    LlmFieldGuess,
)
from veracrawl.external_crawl.normalize_document import normalize_document
from veracrawl.ports.extractor import ExtractionRequest


def _request(html: bytes, url: str = "https://example.com/") -> ExtractionRequest:
    normalized = normalize_document(
        canonical_url=url,
        body=html,
        content_type="text/html",
        raw_artifact_ref="raw-html/abc",
    )
    return ExtractionRequest(
        canonical_url=url,
        normalized_text=normalized.text,
        raw_body=html,
        content_type="text/html",
        raw_artifact_ref="raw-html/abc",
        anchors=list(normalized.anchors),
    )


@dataclass
class _StubCallable:
    response: LlmExtractResponse
    calls: list[ExtractionRequest] | None = None

    def __post_init__(self) -> None:
        self.calls = []

    def __call__(self, request: ExtractionRequest) -> LlmExtractResponse:
        assert self.calls is not None
        self.calls.append(request)
        return self.response


def test_candidate_emitted_when_every_quote_matches_normalised_text() -> None:
    html = b"<html><body><h1>Hello world</h1><p>Specific phrase.</p></body></html>"
    stub = _StubCallable(
        LlmExtractResponse(
            field_guesses=[
                LlmFieldGuess(
                    field_name="headline",
                    value="Hello world",
                    evidence_quote="Hello world",
                ),
                LlmFieldGuess(
                    field_name="excerpt",
                    value="Specific phrase.",
                    evidence_quote="Specific phrase.",
                ),
            ]
        )
    )
    extractor = LlmAssistedExtractor(
        callable=stub, provider_ref="stub", schema_ref="schema:llm-stub/v1"
    )

    result = extractor.extract(_request(html))
    assert result.status == "ok"
    assert len(result.candidates) == 1
    fields = result.candidates[0].fields
    assert fields == {"headline": "Hello world", "excerpt": "Specific phrase."}


def test_candidate_refused_when_quote_not_in_normalised_text() -> None:
    html = b"<html><body><p>Some real content.</p></body></html>"
    stub = _StubCallable(
        LlmExtractResponse(
            field_guesses=[
                LlmFieldGuess(
                    field_name="headline",
                    value="Made up",
                    evidence_quote="A hallucinated phrase that is not on the page.",
                ),
            ]
        )
    )
    extractor = LlmAssistedExtractor(
        callable=stub, provider_ref="stub", schema_ref="schema:llm-stub/v1"
    )

    result = extractor.extract(_request(html))
    # Missing evidence -> no candidate, needs_review status with reason.
    assert result.candidates == []
    assert result.status == "needs_review"
    assert result.reason is not None
    assert "evidence_quote" in result.reason or "match" in result.reason


def test_partial_match_keeps_only_supported_fields() -> None:
    html = b"<html><body><h1>Title here</h1></body></html>"
    stub = _StubCallable(
        LlmExtractResponse(
            field_guesses=[
                LlmFieldGuess(
                    field_name="title",
                    value="Title here",
                    evidence_quote="Title here",
                ),
                LlmFieldGuess(
                    field_name="byline",
                    value="N/A",
                    evidence_quote="Some made up byline",
                ),
            ]
        )
    )
    extractor = LlmAssistedExtractor(
        callable=stub, provider_ref="stub", schema_ref="schema:llm-stub/v1"
    )

    result = extractor.extract(_request(html))
    assert result.status == "ok"
    assert len(result.candidates) == 1
    assert result.candidates[0].fields == {"title": "Title here"}


def test_records_model_call_trace() -> None:
    html = b"<html><body><h1>Hello</h1></body></html>"
    stub = _StubCallable(
        LlmExtractResponse(
            field_guesses=[
                LlmFieldGuess(field_name="title", value="Hello", evidence_quote="Hello")
            ]
        )
    )
    extractor = LlmAssistedExtractor(
        callable=stub, provider_ref="stub", schema_ref="schema:llm-stub/v1"
    )
    extractor.extract(_request(html))

    traces = extractor.recent_traces()
    assert len(traces) == 1
    assert traces[0].provider_ref == "stub"
    assert traces[0].status == "ok"
