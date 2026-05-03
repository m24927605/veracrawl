from __future__ import annotations

import pytest

from veracrawl.contracts.enums import (
    CompletenessResult,
    ProductionRunControlFailureType,
    RunStatus,
)
from veracrawl.control.run_control import run_production_run_control_fixture


def test_success_fixture_completes_with_lifecycle_and_replay_refs() -> None:
    report = run_production_run_control_fixture(
        fixture_id="production-run-control-success",
        scenario="success",
        profile="target",
    )
    assert report.status == RunStatus.COMPLETED
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "production_run_control_completed"
    assert len(report.lifecycle_record_refs) == 2
    assert len(report.event_refs) >= 7
    assert report.replay_refs


def test_paused_resumed_fixture_records_intermediate_lifecycle() -> None:
    report = run_production_run_control_fixture(
        fixture_id="production-run-control-paused-resumed",
        scenario="paused-resumed",
        profile="target",
    )
    assert report.status == RunStatus.COMPLETED
    assert len(report.lifecycle_record_refs) == 4


def test_cancelled_fixture_is_successful_controlled_terminal_state() -> None:
    report = run_production_run_control_fixture(
        fixture_id="production-run-control-cancelled",
        scenario="cancelled",
        profile="target",
    )
    assert report.status == RunStatus.CANCELLED
    assert report.completion_result == CompletenessResult.PASS


@pytest.mark.parametrize(
    ("scenario", "failure"),
    [
        ("policy-denied", ProductionRunControlFailureType.POLICY_DENIED),
        ("missing-approval", ProductionRunControlFailureType.MISSING_APPROVAL),
        ("missing-budget", ProductionRunControlFailureType.MISSING_BUDGET),
        ("invalid-transition", ProductionRunControlFailureType.INVALID_TRANSITION),
        ("missing-replay", ProductionRunControlFailureType.MISSING_REPLAY),
    ],
)
def test_negative_run_control_fixtures_are_typed(
    scenario: str,
    failure: ProductionRunControlFailureType,
) -> None:
    report = run_production_run_control_fixture(
        fixture_id=f"production-run-control-{scenario}",
        scenario=scenario,
        profile="target",
    )
    assert report.completion_result == CompletenessResult.FAIL
    assert report.failure_type == failure
    assert report.operator_status == failure.value
    assert report.diagnostics
