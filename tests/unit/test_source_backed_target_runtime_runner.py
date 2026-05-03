from __future__ import annotations

from pathlib import Path

import pytest

from veracrawl.contracts.enums import (
    CompletenessResult,
    TargetRuntimeFailureType,
    TargetRuntimeStatus,
)
from veracrawl.target_runtime.runner import run_target_runtime_fixture


def test_source_backed_success_derives_refs_from_local_content() -> None:
    fixture_dir = Path("tests/fixtures/source-backed-target-success")
    result = run_target_runtime_fixture(
        fixture_id="source-backed-target-success",
        scenario="source-backed-target-success",
        fixture_dir=fixture_dir,
        source_corpus_ref="corpus.json",
    )
    report = result.report
    assert report.status == TargetRuntimeStatus.COMPLETE
    assert report.completion_result == CompletenessResult.PASS
    assert len(report.source_observation_refs) == 7
    assert len(report.content_hash_refs) == 7
    assert all(ref.startswith("sha256:") for ref in report.content_hash_refs)
    assert report.repair_action_refs
    assert result.source_observations[0].artifact_ref


@pytest.mark.parametrize(
    ("fixture_name", "status", "failure"),
    [
        (
            "source-backed-target-policy-denied",
            TargetRuntimeStatus.BLOCKED,
            TargetRuntimeFailureType.POLICY_DENIED,
        ),
        (
            "source-backed-target-prompt-injection",
            TargetRuntimeStatus.BLOCKED,
            TargetRuntimeFailureType.PROMPT_INJECTION,
        ),
        (
            "source-backed-target-missing-evidence",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.MISSING_EVIDENCE,
        ),
        (
            "source-backed-target-replay-mismatch",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.REPLAY_MISMATCH,
        ),
        (
            "source-backed-target-partial-export",
            TargetRuntimeStatus.FAILED,
            TargetRuntimeFailureType.PARTIAL_EXPORT,
        ),
    ],
)
def test_source_backed_negative_fixtures_are_typed(
    fixture_name: str,
    status: TargetRuntimeStatus,
    failure: TargetRuntimeFailureType,
) -> None:
    fixture_dir = Path("tests/fixtures") / fixture_name
    result = run_target_runtime_fixture(
        fixture_id=fixture_name,
        scenario=fixture_name,
        fixture_dir=fixture_dir,
        source_corpus_ref="corpus.json",
    )
    assert result.report.status == status
    assert result.report.failure_type == failure
    assert result.report.operator_status == failure.value
