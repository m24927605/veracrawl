from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    OpsReplayObservabilityFailureType,
)
from veracrawl.contracts.ops import (
    OpsReplayObservabilityFixtureManifest,
    OpsReplayObservabilityRuntimeReport,
)


def _complete_report(**overrides: object) -> OpsReplayObservabilityRuntimeReport:
    data: dict[str, object] = {
        "id": "ops-replay-observability-runtime-report:unit",
        "fixture_id": "unit-ops-runtime",
        "run_ref": "run:unit",
        "result_publication_export_report_ref": "result-publication:unit",
        "worker_orchestration_runtime_report_ref": "worker-orchestration:unit",
        "ops_console_report_ref": "ops-console:unit",
        "observability_report_ref": "observability:unit",
        "run_control_action_refs": ["run-control:pause", "run-control:resume"],
        "review_item_refs": ["review-item:unit"],
        "evidence_review_refs": ["review-decision:unit"],
        "replay_audit_view_refs": ["replay-audit:unit"],
        "graph_debug_refs": ["graph-debug:unit"],
        "export_status_refs": ["export-status:unit"],
        "withdrawal_status_refs": ["withdrawal-status:unit"],
        "recovery_action_refs": ["recovery:unit"],
        "failure_record_refs": ["failure:unit"],
        "dr_restore_report_refs": ["dr-restore:unit"],
        "quality_report_refs": ["quality:unit"],
        "dashboard_snapshot_refs": ["dashboard:unit"],
        "alert_record_refs": ["alert:unit"],
        "runbook_action_refs": ["runbook:unit"],
        "cost_metric_refs": ["metric:cost"],
        "observability_signal_refs": ["observability-signal:unit"],
        "metric_sample_refs": ["metric:unit"],
        "trace_span_refs": ["trace:unit"],
        "policy_decision_refs": ["policy:unit"],
        "command_record_refs": ["command:unit"],
        "event_cursor_refs": ["event-cursor:unit"],
        "outbox_refs": ["outbox:unit"],
        "redaction_map_refs": ["redaction-map:unit"],
        "replay_bundle_ref": "replay-bundle:unit",
        "operator_status": "ops_replay_observability_completed",
        "completion_result": CompletenessResult.PASS,
    }
    data.update(overrides)
    return OpsReplayObservabilityRuntimeReport(**data)


def test_ops_runtime_report_requires_all_dependency_and_operator_refs() -> None:
    report = _complete_report()
    assert report.completion_result == CompletenessResult.PASS

    with pytest.raises(ValidationError):
        _complete_report(result_publication_export_report_ref=None)

    with pytest.raises(ValidationError):
        _complete_report(observability_signal_refs=[])


def test_ops_runtime_report_rejects_hidden_success_failures() -> None:
    with pytest.raises(ValidationError):
        _complete_report(stale_dashboard_refs=["dashboard:stale"])

    with pytest.raises(ValidationError):
        _complete_report(unsafe_operator_action_refs=["operator-action:unsafe"])

    with pytest.raises(ValidationError):
        _complete_report(replay_gap_refs=["replay-gap:unit"])


def test_ops_runtime_failure_requires_typed_diagnostics() -> None:
    report = OpsReplayObservabilityRuntimeReport(
        id="ops-replay-observability-runtime-report:failure",
        fixture_id="ops-runtime-missing-publication",
        run_ref="run:failure",
        failure_type=OpsReplayObservabilityFailureType.MISSING_PUBLICATION,
        failure_report_refs=["failure:missing-publication"],
        missing_ref_fields=["result_publication_export_report_ref"],
        operator_status=OpsReplayObservabilityFailureType.MISSING_PUBLICATION.value,
        completion_result=CompletenessResult.FAIL,
    )
    assert report.failure_type == OpsReplayObservabilityFailureType.MISSING_PUBLICATION

    with pytest.raises(ValidationError):
        OpsReplayObservabilityRuntimeReport(
            id="ops-replay-observability-runtime-report:bad",
            fixture_id="bad",
            run_ref="run:bad",
            operator_status="bad",
            completion_result=CompletenessResult.FAIL,
        )


def test_ops_runtime_fixture_manifest_validates_negative_cases() -> None:
    manifest = OpsReplayObservabilityFixtureManifest(
        id="ops-runtime-review-replay-success",
        scenario="ops-runtime-review-replay-success",
        profile_refs=["target"],
        expected_completion_result=CompletenessResult.PASS,
        expected_operator_status="ops_replay_observability_completed",
        required_ref_types=["ops_console_report_ref", "observability_report_ref"],
    )
    assert manifest.id == "ops-runtime-review-replay-success"

    with pytest.raises(ValidationError):
        OpsReplayObservabilityFixtureManifest(
            id="ops-runtime-negative-pass",
            scenario="ops-runtime-negative-pass",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.PASS,
            expected_operator_status="bad",
            expected_failure_type=OpsReplayObservabilityFailureType.REPLAY_MISMATCH,
            negative_case=True,
            required_ref_types=["replay_bundle_ref"],
        )

    with pytest.raises(ValidationError):
        OpsReplayObservabilityFixtureManifest(
            id="ops-runtime-missing-required-refs",
            scenario="ops-runtime-missing-required-refs",
            profile_refs=["target"],
            expected_completion_result=CompletenessResult.FAIL,
            expected_operator_status="bad",
            expected_failure_type=OpsReplayObservabilityFailureType.REPLAY_MISMATCH,
            negative_case=True,
        )
