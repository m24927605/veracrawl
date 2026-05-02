"""Deterministic extraction candidate creation."""

from __future__ import annotations

from veracrawl.contracts.common import Ref
from veracrawl.contracts.processing import (
    ExtractionCandidate,
    ExtractionStrategy,
    NormalizedDocument,
    TextAnchor,
)


def build_extraction_strategy(
    *,
    fixture_id: str,
    run_ref: Ref,
    normalized_document: NormalizedDocument,
    policy_decision_refs: list[Ref],
) -> ExtractionStrategy:
    return ExtractionStrategy(
        id=f"extraction-strategy:{fixture_id}",
        run_ref=run_ref,
        schema_ref="schema:process-summary",
        normalized_document_refs=[normalized_document.id],
        field_names=["title", "summary", "link_count"],
        strategy_type="deterministic_html_summary",
        policy_decision_refs=policy_decision_refs,
    )


def create_anchored_candidate(
    *,
    fixture_id: str,
    run_ref: Ref,
    normalized_document: NormalizedDocument,
    anchors: list[TextAnchor],
    strategy: ExtractionStrategy,
    link_count: int,
    omit_anchor_for: str | None = None,
) -> ExtractionCandidate:
    if not anchors:
        raise ValueError("candidate creation requires anchors")
    title_anchor = next((anchor for anchor in anchors if anchor.label == "title"), anchors[0])
    summary_anchor = next(
        (anchor for anchor in anchors if anchor.label in {"h1", "article"}),
        anchors[0],
    )
    field_values: dict[str, object] = {
        "title": title_anchor.text,
        "summary": summary_anchor.text,
        "link_count": link_count,
    }
    field_anchor_refs = {
        "title": title_anchor.id,
        "summary": summary_anchor.id,
        "link_count": summary_anchor.id,
    }
    if omit_anchor_for:
        field_anchor_refs.pop(omit_anchor_for, None)
    return ExtractionCandidate(
        id=f"candidate:{fixture_id}",
        run_ref=run_ref,
        schema_ref=strategy.schema_ref,
        normalized_document_refs=[normalized_document.id],
        field_values=field_values,
        field_anchor_refs=field_anchor_refs,
        confidence_refs=[f"confidence:{fixture_id}:candidate"],
        strategy_ref=strategy.id,
    )
