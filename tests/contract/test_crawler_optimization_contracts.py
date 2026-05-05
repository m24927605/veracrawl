from __future__ import annotations

import pytest

from veracrawl.contracts.crawler_optimization import (
    CrawlerOptimizationManifest,
    ExtractorAttemptRecord,
    FrontierScoringProfile,
)
from veracrawl.contracts.enums import CompletenessResult, CrawlerOptimizationFailureType


def test_frontier_profile_requires_optimization_profile_and_signals() -> None:
    profile = FrontierScoringProfile(
        id="frontier-profile:test",
        profile_refs=["optimization"],
        objective_ref="objective:test",
        scoring_formula_ref="formula:frontier",
        required_signal_refs=["signal:url-pattern"],
    )

    assert profile.stop_confidence_threshold >= profile.confidence_threshold


def test_accepted_extractor_attempt_forbids_llm_output_as_evidence() -> None:
    with pytest.raises(ValueError, match="LLM output cannot be accepted field evidence"):
        ExtractorAttemptRecord(
            id="attempt:1",
            fixture_id="crawler-optimization-success",
            plan_ref="plan:1",
            field_name="price",
            fallback_step="llm_structured",
            fallback_rank=7,
            source_kind="llm_structured",
            raw_value="$99.00",
            normalized_value="99.00 USD",
            confidence=0.92,
            accepted=True,
            source_anchor_ref="anchor:price",
            artifact_ref="artifact:html",
            content_hash_ref="content-hash:html",
            validation_refs=["validator:price"],
            evidence_packet_refs=["evidence:price"],
            llm_output_evidence_refs=["model-output:price"],
        )


def test_crawler_optimization_manifest_separates_positive_and_negative_cases() -> None:
    manifest = CrawlerOptimizationManifest(
        id="crawler-optimization-success",
        scenario="crawler-optimization-success",
        profile_refs=["optimization"],
        objective_ref="objective:test",
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="crawler_optimization_completed",
        required_ref_types=["frontier_score", "replay"],
        algorithm_refs=["algorithm:focused-priority-queue"],
        architecture_refs=["architecture:crawler-intelligence-optimization:v1"],
    )

    assert manifest.expected_failure_type is None

    negative = CrawlerOptimizationManifest(
        id="crawler-optimization-missing-replay",
        scenario="crawler-optimization-missing-replay",
        profile_refs=["optimization"],
        objective_ref="objective:test",
        expected_completion_result=CompletenessResult.FAIL,
        expected_operator_status=CrawlerOptimizationFailureType.MISSING_REPLAY_REFS.value,
        expected_failure_type=CrawlerOptimizationFailureType.MISSING_REPLAY_REFS,
        negative_case=True,
        required_ref_types=["replay"],
        algorithm_refs=["algorithm:cost-recovery-gates"],
        architecture_refs=["architecture:crawler-intelligence-optimization:v1"],
    )

    assert negative.expected_failure_type == CrawlerOptimizationFailureType.MISSING_REPLAY_REFS
