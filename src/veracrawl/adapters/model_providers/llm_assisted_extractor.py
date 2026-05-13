"""``LlmAssistedExtractor`` — Phase 5 LLM extractor adapter boundary.

The adapter sits behind a narrow :class:`LlmExtractCallable` callable
so the core has no static dependency on any LLM SDK. The actual
LLM call is whatever the operator wires in: a real provider via
``ModelProviderPortV2``, a recorded fixture, or a stub. Inside this
module we treat the callable as an opaque function from
``ExtractionRequest`` to :class:`LlmExtractResponse`.

The adapter enforces the goal-doc policy that **LLM output cannot
become source evidence**: every ``LlmFieldGuess`` must carry an
``evidence_quote`` that occurs verbatim inside the request's
``normalized_text``. Guesses whose quotes don't match are dropped.
A request with zero supported guesses returns ``status="needs_review"``
rather than fabricating an empty candidate.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from veracrawl.external_crawl.normalize_document import NormalizedDocumentAnchor
from veracrawl.external_crawl.traces import ModelCallTrace
from veracrawl.ports.extractor import (
    ExtractionCandidate,
    ExtractionRequest,
    ExtractionResult,
)


@dataclass(frozen=True, slots=True)
class LlmFieldGuess:
    field_name: str
    value: str
    evidence_quote: str


@dataclass(frozen=True, slots=True)
class LlmExtractResponse:
    field_guesses: list[LlmFieldGuess] = field(default_factory=list)


class LlmExtractCallable(Protocol):
    """Minimal LLM-call surface: takes a request, returns guesses + quotes."""

    def __call__(self, request: ExtractionRequest) -> LlmExtractResponse: ...


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _anchor_covering_quote(
    quote: str, normalized_text: str, anchors: list[NormalizedDocumentAnchor]
) -> NormalizedDocumentAnchor | None:
    idx = normalized_text.find(quote)
    if idx < 0:
        return None
    end = idx + len(quote)
    for anchor in anchors:
        if anchor.char_offset_start <= idx and anchor.char_offset_end >= end:
            return anchor
    return None


@dataclass(slots=True)
class LlmAssistedExtractor:
    callable: LlmExtractCallable
    provider_ref: str
    schema_ref: str
    _traces: list[ModelCallTrace] = field(default_factory=list)

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        started = datetime.now(tz=UTC)
        started_ms = time.monotonic()
        prompt_repr = (
            f"schema={self.schema_ref}\n"
            f"text={request.normalized_text}\n"
            f"content_type={request.content_type}\n"
            f"url={request.canonical_url}"
        )
        try:
            response = self.callable(request)
            status = "ok"
            response_repr = "".join(
                f"{g.field_name}|{g.value}|{g.evidence_quote}\n"
                for g in response.field_guesses
            )
        except Exception as exc:
            completed = datetime.now(tz=UTC)
            self._traces.append(
                ModelCallTrace(
                    trace_id=f"llm:{self.provider_ref}:{int(started.timestamp() * 1000)}",
                    canonical_url=request.canonical_url,
                    provider_ref=self.provider_ref,
                    schema_ref=self.schema_ref,
                    prompt_hash=_sha256(prompt_repr),
                    response_hash=_sha256(repr(exc)),
                    status="error",
                    started_at=started,
                    completed_at=completed,
                    elapsed_ms=(time.monotonic() - started_ms) * 1000.0,
                )
            )
            return ExtractionResult(
                canonical_url=request.canonical_url,
                candidates=[],
                status="needs_review",
                reason=f"llm callable raised: {exc!r}",
            )

        completed = datetime.now(tz=UTC)
        self._traces.append(
            ModelCallTrace(
                trace_id=f"llm:{self.provider_ref}:{int(started.timestamp() * 1000)}",
                canonical_url=request.canonical_url,
                provider_ref=self.provider_ref,
                schema_ref=self.schema_ref,
                prompt_hash=_sha256(prompt_repr),
                response_hash=_sha256(response_repr),
                status=status,
                started_at=started,
                completed_at=completed,
                elapsed_ms=(time.monotonic() - started_ms) * 1000.0,
            )
        )

        supported_fields: dict[str, object] = {}
        supporting_anchors: list[NormalizedDocumentAnchor] = []
        unsupported: list[str] = []
        for guess in response.field_guesses:
            anchor = _anchor_covering_quote(
                guess.evidence_quote, request.normalized_text, list(request.anchors)
            )
            if anchor is None:
                unsupported.append(guess.field_name)
                continue
            supported_fields[guess.field_name] = guess.value
            supporting_anchors.append(anchor)

        if not supported_fields:
            return ExtractionResult(
                canonical_url=request.canonical_url,
                candidates=[],
                status="needs_review",
                reason=(
                    "LLM response had no field guesses whose evidence_quote "
                    "matched the normalised text; refusing to publish without "
                    "source evidence"
                ),
            )

        # Deduplicate anchors by identity.
        anchors_unique: list[NormalizedDocumentAnchor] = []
        seen: set[tuple[int, int, str]] = set()
        for anchor in supporting_anchors:
            key = (anchor.char_offset_start, anchor.char_offset_end, anchor.text_hash)
            if key not in seen:
                seen.add(key)
                anchors_unique.append(anchor)

        candidate = ExtractionCandidate(
            canonical_url=request.canonical_url,
            schema_ref=self.schema_ref,
            fields=supported_fields,
            evidence_anchors=anchors_unique,
        )
        return ExtractionResult(
            canonical_url=request.canonical_url,
            candidates=[candidate],
            status="ok",
            reason=(
                None
                if not unsupported
                else f"dropped fields without supporting evidence: {unsupported}"
            ),
        )

    def recent_traces(self) -> list[ModelCallTrace]:
        return list(self._traces)


__all__ = [
    "LlmAssistedExtractor",
    "LlmExtractCallable",
    "LlmExtractResponse",
    "LlmFieldGuess",
]
