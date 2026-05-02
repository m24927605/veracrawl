"""Runtime extraction owner service."""

from __future__ import annotations

from veracrawl.contracts.enums import OwnerService
from veracrawl.contracts.objective import CrawlRun
from veracrawl.contracts.processing import ExtractionCandidate, NormalizedDocument
from veracrawl.control.runtime import require_owner


def extract_candidate(
    *,
    run: CrawlRun,
    normalized_document: NormalizedDocument,
    owner: OwnerService = OwnerService.EXTRACT,
) -> ExtractionCandidate:
    require_owner(
        actual_owner=owner,
        expected_owner=OwnerService.EXTRACT,
        target_ref=f"candidate:{run.id}",
    )
    return ExtractionCandidate(
        id=f"candidate:{run.id}",
        run_ref=run.id,
        schema_ref="schema:record-output",
        normalized_document_refs=[normalized_document.id],
        field_values={"name": "Fixture Product", "price": "19.99", "currency": "USD"},
        field_anchor_refs={
            "name": f"anchor:{normalized_document.id}:name",
            "price": f"anchor:{normalized_document.id}:price",
            "currency": f"anchor:{normalized_document.id}:currency",
        },
        confidence_refs=[f"confidence:{run.id}:extract"],
        strategy_ref="strategy:runtime-fixture",
    )
