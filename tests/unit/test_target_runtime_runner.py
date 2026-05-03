from __future__ import annotations

import pytest

from veracrawl.contracts.enums import (
    CompletenessResult,
    TargetRuntimeFailureType,
    TargetRuntimeStatus,
    TargetWebsitePattern,
)
from veracrawl.target_runtime.runner import run_target_runtime_fixture


def test_target_runtime_success_covers_multi_pattern_runtime_path() -> None:
    result = run_target_runtime_fixture(
        fixture_id="target-runtime-success",
        scenario="target-runtime-success",
    )
    report = result.report
    assert report.status == TargetRuntimeStatus.COMPLETE
    assert report.completion_result == CompletenessResult.PASS
    assert len(set(report.covered_patterns)) >= 7
    assert TargetWebsitePattern.SITEMAP_RSS_FEED in report.covered_patterns
    assert TargetWebsitePattern.LISTING_DETAIL in report.covered_patterns
    assert TargetWebsitePattern.API_LIKE_ENDPOINTS in report.covered_patterns
    assert report.evidence_refs
    assert report.graph_refs
    assert report.export_receipt_refs
    assert report.replay_bundle_ref


def test_target_runtime_drift_repair_uses_framework_neutral_ai_record() -> None:
    result = run_target_runtime_fixture(
        fixture_id="target-runtime-drift-repair",
        scenario="target-runtime-drift-repair",
    )
    report = result.report
    assert report.status == TargetRuntimeStatus.COMPLETE
    assert report.operator_status == "target_runtime_drift_repaired"
    assert report.repair_action_refs
    repair_record = result.ai_recommendations[0]
    assert repair_record.accepted is True
    assert repair_record.repair_frontier_refs
    assert not repair_record.framework_native_state_refs


def test_target_runtime_needs_review_cannot_claim_complete() -> None:
    result = run_target_runtime_fixture(
        fixture_id="target-runtime-needs-review",
        scenario="target-runtime-needs-review",
    )
    assert result.report.status == TargetRuntimeStatus.NEEDS_REVIEW
    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.review_item_refs
    assert result.report.operator_status == "target_runtime_needs_review"


@pytest.mark.parametrize(
    ("scenario", "status", "failure"),
    [
        (
            "target-runtime-policy-denied",
            TargetRuntimeStatus.BLOCKED,
            TargetRuntimeFailureType.POLICY_DENIED,
        ),
        (
            "target-runtime-prompt-injection",
            TargetRuntimeStatus.BLOCKED,
            TargetRuntimeFailureType.PROMPT_INJECTION,
        ),
        (
            "target-runtime-missing-evidence",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.MISSING_EVIDENCE,
        ),
        (
            "target-runtime-replay-mismatch",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.REPLAY_MISMATCH,
        ),
        (
            "target-runtime-partial-export",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.PARTIAL_EXPORT,
        ),
        (
            "target-runtime-false-complete",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.FALSE_COMPLETE,
        ),
    ],
)
def test_target_runtime_negative_scenarios_have_typed_failures(
    scenario: str,
    status: TargetRuntimeStatus,
    failure: TargetRuntimeFailureType,
) -> None:
    result = run_target_runtime_fixture(fixture_id=scenario, scenario=scenario)
    assert result.report.status == status
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.failure_type == failure
    assert result.report.operator_status == failure.value
    assert result.report.failure_report_refs
