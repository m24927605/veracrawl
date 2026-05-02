from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    ObservabilityMetricKind,
    ObservabilitySignalType,
    OpsSeverity,
    RunbookActionStatus,
)
from veracrawl.contracts.ops import (
    ObservabilityFixtureManifest,
    ObservabilityReport,
    ObservabilitySignal,
    RunbookAction,
)


def test_observability_report_pass_requires_canonical_refs() -> None:
    with pytest.raises(ValidationError):
        ObservabilityReport(
            id="observability-report:bad",
            run_ref="run:bad",
            signal_refs=["observability-signal:bad"],
            metric_sample_refs=["metric-sample:bad"],
            trace_span_refs=["trace-span:bad"],
            alert_record_refs=["alert:bad"],
            runbook_action_refs=["runbook-action:bad"],
            quality_report_refs=["quality-report:bad"],
            cost_metric_refs=["metric-sample:bad:cost"],
            dashboard_snapshot_refs=["ops-dashboard-snapshot:bad"],
            projection_watermark_refs=["projection-watermark:bad"],
            failure_record_refs=["failure-record:bad"],
            recovery_action_refs=["recovery-action:bad"],
            dr_restore_report_refs=["dr-restore-report:bad"],
            policy_decision_refs=["policy:bad:observability"],
            command_record_refs=["command:bad:observability"],
            event_cursor_refs=["event-cursor:bad:observability"],
            outbox_refs=["outbox:bad:observability"],
            redaction_map_refs=["redaction-map:bad"],
            replay_bundle_ref="replay-bundle:bad",
            operator_status="operational_observability_completed",
            result=CompletenessResult.PASS,
        )


def test_observability_signal_rejects_unredacted_sensitive_payload_refs() -> None:
    with pytest.raises(ValidationError):
        ObservabilitySignal(
            id="observability-signal:bad",
            signal_type=ObservabilitySignalType.FAILURE,
            owner_service_ref="ops:observability",
            severity=OpsSeverity.HIGH,
            run_ref="run:bad",
            source_ref="ops-console-report:bad",
            metric_refs=["metric-sample:bad"],
            trace_refs=["trace-span:bad"],
            alert_refs=["alert:bad"],
            policy_decision_refs=["policy:bad:observability"],
            redaction_map_refs=["redaction-map:bad"],
            replay_bundle_ref="replay-bundle:bad",
            payload_refs=["raw_prompt:leaked"],
        )


def test_side_effecting_runbook_action_requires_approval() -> None:
    with pytest.raises(ValidationError):
        RunbookAction(
            id="runbook-action:bad",
            action_type="refresh_dashboard_projection",
            status=RunbookActionStatus.EXECUTED,
            run_ref="run:bad",
            alert_ref="alert:bad",
            failure_record_refs=["failure-record:bad"],
            side_effecting=True,
            policy_decision_refs=["policy:bad:observability"],
            command_refs=["command:bad:refresh"],
            event_refs=["event:bad:refresh"],
            replay_bundle_ref="replay-bundle:bad",
        )


def test_observability_fixture_manifest_rejects_negative_pass() -> None:
    with pytest.raises(ValidationError):
        ObservabilityFixtureManifest(
            id="observability-bad",
            scenario="observability-bad",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            negative_case=True,
        )


def test_metric_kind_contract_exposes_quality_and_cost() -> None:
    assert ObservabilityMetricKind.COST.value == "cost"
    assert ObservabilityMetricKind.QUALITY.value == "quality"
