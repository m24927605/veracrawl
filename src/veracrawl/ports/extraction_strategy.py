"""``ExtractionStrategyPort`` — open-schema discovery port (s7).

Given a normalized document (refs-only ``NormalizedDocumentReadModel``)
and the crawl run reference, the strategy proposes candidate fields
to extract. The deterministic fixture adapter is
``AnchorFrequencyExtractionStrategy``; the LLM adapter lands in s9.

See ``docs/plans/general-purpose-crawler-agentification/
s7-extraction-strategy-port.md``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.common import Ref
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.contracts.schema_proposal import SchemaProposal


@runtime_checkable
class ExtractionStrategyPort(Protocol):
    def propose(
        self,
        *,
        document: NormalizedDocumentReadModel,
        run_ref: Ref,
    ) -> SchemaProposal: ...


__all__ = ["ExtractionStrategyPort"]
