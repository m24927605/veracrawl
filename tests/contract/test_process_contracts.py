from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.processing import (
    AnchorMap,
    ExtractionCandidate,
    NormalizeExtractReport,
    TextAnchor,
)


def test_anchor_requires_positive_span() -> None:
    with pytest.raises(ValidationError):
        TextAnchor(
            id="anchor:bad",
            normalized_document_ref="doc:1",
            raw_artifact_ref="artifact:raw",
            label="h1",
            text="Title",
            normalized_start=5,
            normalized_end=5,
            selector_ref="selector:h1",
        )


def test_anchor_map_requires_anchors() -> None:
    with pytest.raises(ValidationError):
        AnchorMap(
            id="anchor-map:bad",
            normalized_document_ref="doc:1",
            raw_artifact_ref="artifact:raw",
            content_digest="digest",
        )


def test_candidate_requires_field_anchors() -> None:
    with pytest.raises(ValidationError):
        ExtractionCandidate(
            id="candidate:bad",
            run_ref="run:1",
            schema_ref="schema:1",
            normalized_document_refs=["doc:1"],
            field_values={"name": "Missing anchor"},
            field_anchor_refs={},
            strategy_ref="strategy:1",
        )


def test_process_report_requires_refs_when_passing() -> None:
    with pytest.raises(ValidationError):
        NormalizeExtractReport(
            id="process-report:bad",
            run_ref="run:1",
            operator_status="process_completed",
            completion_result=CompletenessResult.PASS,
        )
