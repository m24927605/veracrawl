from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    OpsDashboardType,
    ReplayMode,
    ReviewItemStatus,
    ReviewItemType,
    ReviewPriority,
)
from veracrawl.contracts.ops import (
    DRRestoreReport,
    OpsConsoleReport,
    OpsDashboardSnapshot,
    QualityReport,
    ReplayAuditView,
    ReviewItem,
)


def test_review_item_requires_evidence_input_and_policy_refs() -> None:
    item = ReviewItem(
        id="review-item:unit",
        run_id="run:unit",
        objective_id="objective:unit",
        item_type=ReviewItemType.EVIDENCE_PACKET,
        input_refs=["evidence:unit"],
        reason="needs_review",
        priority=ReviewPriority.HIGH,
        status=ReviewItemStatus.OPEN,
        policy_decision_refs=["policy:unit:review"],
    )
    assert item.input_refs
    with pytest.raises(ValidationError):
        ReviewItem(
            id="review-item:bad",
            run_id="run:bad",
            objective_id="objective:bad",
            item_type=ReviewItemType.EVIDENCE_PACKET,
            reason="missing evidence",
            priority=ReviewPriority.HIGH,
            status=ReviewItemStatus.OPEN,
            policy_decision_refs=["policy:bad:review"],
        )


def test_replay_audit_pass_requires_replay_refs() -> None:
    with pytest.raises(ValidationError):
        ReplayAuditView(
            id="replay-audit:bad",
            run_id="run:bad",
            replay_bundle_ref="replay-bundle:bad",
            replay_mode=ReplayMode.STRUCTURAL,
            replay_validation_report_ref="replay-validation:bad",
            redaction_map_ref="redaction-map:bad",
            policy_decision_refs=["policy:bad:replay"],
            completeness_result=CompletenessResult.PASS,
        )


def test_quality_report_rejects_invalid_rates() -> None:
    with pytest.raises(ValidationError):
        QualityReport(
            id="quality-report:bad",
            run_id="run:bad",
            pages_fetched=1,
            candidates_created=1,
            outputs_published=1,
            verification_decisions_accepted=1,
            verification_decisions_rejected=0,
            factual_outputs_published=1,
            conflicts_detected=0,
            drift_events=0,
            freshness_lag_seconds=1,
            extraction_success_rate=1.2,
            verification_acceptance_rate=1.0,
            policy_decision_refs=["policy:bad:quality"],
            projection_watermark_refs=["projection-watermark:bad"],
        )


def test_dashboard_pass_rejects_stale_projection() -> None:
    with pytest.raises(ValidationError):
        OpsDashboardSnapshot(
            id="dashboard:bad",
            run_id="run:bad",
            dashboard_type=OpsDashboardType.QUALITY,
            as_of_event_cursor_refs=["event-cursor:bad"],
            projection_watermark_refs=["projection-watermark:bad"],
            quality_report_refs=["quality-report:bad"],
            freshness_lag_seconds=10,
            stale_projection_refs=["projection-watermark:stale"],
            completion_result=CompletenessResult.PASS,
        )


def test_dr_restore_pass_requires_complete_restore_refs() -> None:
    with pytest.raises(ValidationError):
        DRRestoreReport(
            id="dr-restore-report:bad",
            restore_scope_ref="restore-scope:bad",
            dr_restore_plan_id="plan:bad",
            dr_restore_run_id="run:bad",
            metadata_restore_ref="metadata:bad",
            artifact_reachability_report_ref="artifact:bad",
            event_replay_report_ref="event-replay:bad",
            data_loss_detected=False,
            result=CompletenessResult.PASS,
        )


def test_ops_console_report_pass_requires_replay_refs() -> None:
    with pytest.raises(ValidationError):
        OpsConsoleReport(
            id="ops-console-report:bad",
            run_ref="run:bad",
            review_item_refs=["review-item:bad"],
            replay_audit_view_refs=["replay-audit:bad"],
            quality_report_refs=["quality-report:bad"],
            dashboard_snapshot_ref="dashboard:bad",
            dr_restore_report_refs=["dr-restore-report:bad"],
            policy_decision_refs=["policy:bad:ops"],
            operator_status="ops_console_completed",
            completion_result=CompletenessResult.PASS,
        )
