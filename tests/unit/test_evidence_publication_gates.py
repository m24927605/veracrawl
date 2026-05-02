from __future__ import annotations

from tests.helpers.runtime_fixture_assertions import (
    assert_negative_runtime_report,
    assert_successful_runtime_report,
)
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.control.runtime import run_runtime_fixture


def test_successful_publication_requires_evidence_verification_policy_and_replay() -> None:
    report = run_runtime_fixture(
        fixture_id="runtime-record-success",
        scenario="record-success",
        profile="target",
    )
    assert_successful_runtime_report(report)


def test_missing_evidence_blocks_publication_with_needs_review() -> None:
    report = run_runtime_fixture(
        fixture_id="runtime-missing-evidence",
        scenario="missing-evidence",
        profile="target",
    )
    assert_negative_runtime_report(
        report,
        operator_status="missing_evidence",
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )


def test_verification_conflict_blocks_publication() -> None:
    report = run_runtime_fixture(
        fixture_id="runtime-verification-conflict",
        scenario="verification-conflict",
        profile="target",
    )
    assert_negative_runtime_report(
        report,
        operator_status="verification_conflict",
        completion_result=CompletenessResult.FAIL,
    )


def test_policy_blocked_source_blocks_publication() -> None:
    report = run_runtime_fixture(
        fixture_id="runtime-blocked-source",
        scenario="blocked-source",
        profile="target",
    )
    assert_negative_runtime_report(
        report,
        operator_status="source_blocked",
        completion_result=CompletenessResult.FAIL,
    )
