"""``NormalizedDocumentReadModel`` — refs-only view of a normalized document.

s7 (extraction-strategy port) consumes a read model rather than the
runtime ``external_crawl.normalize_document`` dataclass so the port
boundary stays clean: the consumer (e.g.,
``AnchorFrequencyExtractionStrategy``) receives URLs/refs and uses a
caller-injected ``resolve_text(ref) -> str`` closure to read sample
bytes via ``ArtifactStorePort.read``. The s10 schema-extraction
runtime later reuses the same shape.

Distinct from:

* ``veracrawl.contracts.processing.NormalizedDocument`` — a different
  (refs-only) processing contract.
* ``veracrawl.external_crawl.normalize_document.NormalizedDocument`` —
  the runtime in-memory dataclass produced by the FIFO normalizer.

See ``docs/plans/general-purpose-crawler-agentification/
s7-extraction-strategy-port.md``.
"""

from __future__ import annotations

from pydantic import Field

from veracrawl.contracts.common import Ref, VeraModel


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


class NormalizedDocumentReadModel(VeraModel):
    """Refs-only view of one normalized document fed to s7/s10."""

    id: str
    normalized_document_ref: Ref
    text_sample_refs: list[Ref] = Field(default_factory=list)

    def model_post_init(self, __context: object) -> None:
        _require(bool(self.id.strip()), "id must be non-blank")
        _require(
            bool(self.normalized_document_ref.strip()),
            "normalized_document_ref must be non-blank",
        )
        _require(
            len(self.text_sample_refs) >= 1,
            "text_sample_refs must contain ≥ 1 ref",
        )
        for ref in self.text_sample_refs:
            _require(bool(ref.strip()), "text_sample_refs entries must be non-blank")


__all__ = ["NormalizedDocumentReadModel"]
