from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.extract.candidates import build_extraction_strategy, create_anchored_candidate
from veracrawl.normalize.pipeline import NormalizationResult, normalize_html_document


def _normalized() -> NormalizationResult:
    return normalize_html_document(
        fixture_id="unit-candidate",
        run_ref="run:unit-candidate",
        source_adapter_result_ref="source-result:unit",
        source_url="http://example.test/static/basic",
        raw_artifact_ref="artifact:raw",
        raw_html="<html><title>Title</title><body><h1>Hello</h1></body></html>",
        policy_decision_refs=["policy:process"],
    )


def test_candidate_has_anchors_for_every_field() -> None:
    normalized = _normalized()
    strategy = build_extraction_strategy(
        fixture_id="unit-candidate",
        run_ref="run:unit-candidate",
        normalized_document=normalized.normalized_document,
        policy_decision_refs=["policy:process"],
    )
    candidate = create_anchored_candidate(
        fixture_id="unit-candidate",
        run_ref="run:unit-candidate",
        normalized_document=normalized.normalized_document,
        anchors=normalized.anchors,
        strategy=strategy,
        link_count=len(normalized.link_provenance),
    )
    assert set(candidate.field_values) == set(candidate.field_anchor_refs)


def test_candidate_anchor_gap_is_rejected() -> None:
    normalized = _normalized()
    strategy = build_extraction_strategy(
        fixture_id="unit-candidate-gap",
        run_ref="run:unit-candidate-gap",
        normalized_document=normalized.normalized_document,
        policy_decision_refs=["policy:process"],
    )
    with pytest.raises(ValidationError):
        create_anchored_candidate(
            fixture_id="unit-candidate-gap",
            run_ref="run:unit-candidate-gap",
            normalized_document=normalized.normalized_document,
            anchors=normalized.anchors,
            strategy=strategy,
            link_count=0,
            omit_anchor_for="summary",
        )
