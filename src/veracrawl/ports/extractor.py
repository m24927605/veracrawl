"""Extractor port for the external-crawl Phase 4 runtime.

Every extractor implementation (deterministic, link-graph, document
metadata, LLM-assisted, …) produces :class:`ExtractionCandidate`
records that carry the extracted fields *plus* the evidence anchors
they cite. A candidate with no evidence anchors fails contract
validation — there is no path for an extractor to publish a field
without a verifiable source span.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import Field, model_validator

from veracrawl.contracts.common import VeraModel
from veracrawl.external_crawl.normalize_document import NormalizedDocumentAnchor


class ExtractionRequest(VeraModel):
    model_config = {"arbitrary_types_allowed": True, "extra": "forbid"}

    canonical_url: str = Field(min_length=1)
    normalized_text: str
    raw_body: bytes
    content_type: str
    raw_artifact_ref: str = Field(min_length=1)
    anchors: list[NormalizedDocumentAnchor]


class ExtractionCandidate(VeraModel):
    canonical_url: str = Field(min_length=1)
    schema_ref: str = Field(min_length=1)
    fields: dict[str, object]
    evidence_anchors: list[NormalizedDocumentAnchor]

    @model_validator(mode="after")
    def require_evidence(self) -> ExtractionCandidate:
        if not self.evidence_anchors:
            raise ValueError(
                "extraction candidate requires at least one evidence_anchors entry"
            )
        if not self.fields:
            raise ValueError("extraction candidate fields must be non-empty")
        return self


class ExtractionResult(VeraModel):
    canonical_url: str = Field(min_length=1)
    candidates: list[ExtractionCandidate]
    status: str  # "ok" | "needs_review"
    reason: str | None = None

    @model_validator(mode="after")
    def validate_status(self) -> ExtractionResult:
        if self.status not in {"ok", "needs_review"}:
            raise ValueError(f"unsupported extraction status: {self.status!r}")
        return self


class ExtractorPort(Protocol):
    def extract(self, request: ExtractionRequest) -> ExtractionResult: ...


__all__ = [
    "ExtractionCandidate",
    "ExtractionRequest",
    "ExtractionResult",
    "ExtractorPort",
]
