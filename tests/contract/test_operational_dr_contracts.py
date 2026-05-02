from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    DRRestorePhase,
    DRRestorePhaseStatus,
    DRRestoreRunStatus,
)
from veracrawl.contracts.ops import (
    DRRestoreFixtureManifest,
    DRRestorePhaseResult,
    DRRestorePlan,
    DRRestorePlanPhase,
    DRRestoreReport,
    DRRestoreRun,
)
from veracrawl.runtime_support.disaster_recovery import dr_restore_plan


def test_dr_restore_plan_requires_all_ordered_phases() -> None:
    plan = dr_restore_plan(
        "unit",
        policy_decision_refs=["policy:unit:dr"],
        approval_decision_refs=["approval:unit:dr"],
    )
    assert {phase.phase_name for phase in plan.ordered_phases} == set(DRRestorePhase)
    assert [phase.phase_order for phase in plan.ordered_phases] == list(
        range(1, len(DRRestorePhase) + 1)
    )
    with pytest.raises(ValidationError):
        DRRestorePlan(
            id="dr-restore-plan:bad",
            restore_scope_ref="restore-scope:bad",
            restore_point_ref="restore-point:bad",
            backup_manifest_ref="backup-manifest:bad",
            metadata_snapshot_ref="metadata-snapshot:bad",
            artifact_snapshot_refs=["artifact-snapshot:bad"],
            event_cursor_refs=["event-cursor:bad"],
            ordered_phases=[
                DRRestorePlanPhase(
                    phase_name=DRRestorePhase.RESTORE_METADATA,
                    phase_order=1,
                    input_refs=["input:bad"],
                    output_contract_refs=["output-contract:bad"],
                    validation_gate_refs=["validation-gate:bad"],
                )
            ],
            required_validation_gate_refs=["validation-gate:bad"],
            policy_decision_refs=["policy:bad:dr"],
            approval_decision_refs=["approval:bad:dr"],
        )


def test_dr_restore_run_requires_completed_phase_refs() -> None:
    with pytest.raises(ValidationError):
        DRRestoreRun(
            id="dr-restore-run:bad",
            dr_restore_plan_id="dr-restore-plan:bad",
            restore_scope_ref="restore-scope:bad",
            phase_results=[
                DRRestorePhaseResult(
                    phase_name=DRRestorePhase.RESTORE_METADATA,
                    status=DRRestorePhaseStatus.COMPLETED,
                    input_refs=["input:bad"],
                    output_refs=["output:bad"],
                    validation_result_refs=["validation:bad"],
                )
            ],
            current_phase=DRRestorePhase.PUBLISH_REPORT,
            status=DRRestoreRunStatus.COMPLETED,
            emitted_event_refs=["event:bad:dr_restore_reported"],
            policy_decision_refs=["policy:bad:dr"],
        )


def test_operational_dr_report_pass_requires_integrated_refs() -> None:
    with pytest.raises(ValidationError):
        DRRestoreReport(
            id="dr-restore-report:bad",
            restore_scope_ref="restore-scope:bad",
            dr_restore_plan_id="dr-restore-plan:bad",
            dr_restore_run_id="dr-restore-run:bad",
            restore_point_ref="restore-point:bad",
            backup_manifest_ref="backup-manifest:bad",
            metadata_restore_ref="metadata-restore:bad",
            artifact_reachability_report_ref="artifact-reachability:bad",
            event_replay_report_ref="event-replay:bad",
            projection_rebuild_job_refs=["projection-rebuild-job:bad"],
            validation_refs=["validation:bad"],
            policy_decision_refs=["policy:bad:dr"],
            data_loss_detected=False,
            operator_status="operational_dr_restore_completed",
            result=CompletenessResult.PASS,
        )


def test_dr_restore_fixture_manifest_rejects_negative_pass() -> None:
    with pytest.raises(ValidationError):
        DRRestoreFixtureManifest(
            id="dr-restore-bad",
            scenario="dr-restore-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            negative_case=True,
        )
