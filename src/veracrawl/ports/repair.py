"""``RepairPort`` — propose alternative xpaths for drifted fields (s8)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from veracrawl.contracts.common import Ref
from veracrawl.contracts.drift_report import DriftReport
from veracrawl.contracts.normalized_document_read_model import (
    NormalizedDocumentReadModel,
)
from veracrawl.contracts.repair_proposal import RepairProposal


@runtime_checkable
class RepairPort(Protocol):
    def repair(
        self,
        *,
        drift_report: DriftReport,
        document_samples: list[NormalizedDocumentReadModel],
        resolve_text: Callable[[Ref], str],
        run_ref: Ref,
    ) -> RepairProposal: ...


__all__ = ["RepairPort"]
