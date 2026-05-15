"""``DriftDetectionPort`` — aggregate ``ExtractionOutcome`` → ``DriftReport`` (s8)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.common import Ref
from veracrawl.contracts.drift_report import DriftReport
from veracrawl.contracts.extraction_outcome import ExtractionOutcome
from veracrawl.contracts.schema_proposal import SchemaProposal


@runtime_checkable
class DriftDetectionPort(Protocol):
    def detect(
        self,
        *,
        proposal: SchemaProposal,
        extraction_outcomes: list[ExtractionOutcome],
        run_ref: Ref,
    ) -> DriftReport: ...


__all__ = ["DriftDetectionPort"]
