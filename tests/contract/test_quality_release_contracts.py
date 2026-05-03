from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    QualityReleaseDecision,
    QualityReleaseGateType,
)
from veracrawl.contracts.quality_release import (
    QualityReleaseGateRef,
    QualityReleaseManifest,
    QualityReleaseReport,
    QualityReleaseStabilityRun,
    QualityReleaseThresholds,
)


def _gate_ref() -> QualityReleaseGateRef:
    return QualityReleaseGateRef(
        id="quality-release-gate-ref:1",
        gate_type=QualityReleaseGateType.REPAIR_SUCCESS,
        report_ref="repair-quality-report:1",
        completion_result=CompletenessResult.PASS,
        replay_bundle_ref="replay:gate:1",
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
    )


def _stability_run() -> QualityReleaseStabilityRun:
    return QualityReleaseStabilityRun(
        id="quality-release-stability-run:1",
        run_ref="run:1",
        total_cost_usd=0.5,
        p95_latency_ms=3200,
        throughput_pages_per_minute=42.0,
        retry_rate=0.04,
        token_count=40000,
        model_call_count=80,
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        slo_metric_refs=["slo:1"],
        replay_bundle_ref="replay:run:1",
    )


def test_quality_release_threshold_defaults_are_release_blocking() -> None:
    thresholds = QualityReleaseThresholds(id="thresholds:1")

    assert thresholds.required_quality_gate_count == 6
    assert thresholds.min_stability_run_count == 3
    assert thresholds.max_total_cost_usd == 2.50
    assert thresholds.max_retry_rate == 0.10


def test_quality_release_gate_ref_requires_pass_and_replay() -> None:
    with pytest.raises(ValidationError):
        QualityReleaseGateRef(
            id="quality-release-gate-ref:1",
            gate_type=QualityReleaseGateType.REPAIR_SUCCESS,
            report_ref="repair-quality-report:1",
            completion_result=CompletenessResult.FAIL,
            replay_bundle_ref="replay:gate:1",
            policy_decision_refs=["policy:1"],
            command_record_refs=["command:1"],
            event_cursor_refs=["event-cursor:1"],
            outbox_refs=["outbox:1"],
        )


def test_quality_release_stability_run_requires_slo_and_replay_refs() -> None:
    with pytest.raises(ValidationError):
        QualityReleaseStabilityRun(
            id="quality-release-stability-run:1",
            run_ref="run:1",
            total_cost_usd=0.5,
            p95_latency_ms=3200,
            throughput_pages_per_minute=42.0,
            retry_rate=0.04,
            token_count=40000,
            model_call_count=80,
            policy_decision_refs=["policy:1"],
            command_record_refs=["command:1"],
            event_cursor_refs=["event-cursor:1"],
            outbox_refs=["outbox:1"],
            slo_metric_refs=[],
            replay_bundle_ref="replay:run:1",
        )


def test_quality_release_report_requires_all_refs_to_pass() -> None:
    gate_ref = _gate_ref()
    stability_run = _stability_run()
    report = QualityReleaseReport(
        id="quality-release-report:1",
        fixture_id="quality-release-ready",
        run_ref="run:release",
        thresholds_ref="thresholds:1",
        quality_gate_refs=[gate_ref.id],
        stability_run_refs=[stability_run.id],
        required_quality_gate_count=1,
        observed_quality_gate_count=1,
        stability_run_count=1,
        total_cost_usd=0.5,
        p95_latency_ms=3200,
        throughput_pages_per_minute=42.0,
        retry_rate=0.04,
        token_count=40000,
        model_call_count=80,
        gate_report_refs=[gate_ref.report_ref],
        policy_decision_refs=["policy:1"],
        command_record_refs=["command:1"],
        event_cursor_refs=["event-cursor:1"],
        outbox_refs=["outbox:1"],
        slo_metric_refs=["slo:1"],
        audit_report_refs=["audit:1"],
        release_decision_refs=["release-decision:1"],
        replay_bundle_refs=["replay:1"],
        release_decision=QualityReleaseDecision.RELEASE_READY,
        completion_result=CompletenessResult.PASS,
    )

    assert report.release_decision == QualityReleaseDecision.RELEASE_READY


def test_quality_release_manifest_supports_quality_profile() -> None:
    manifest = QualityReleaseManifest(
        id="quality-release-ready",
        scenario="quality-release-ready",
        profile_refs=["quality"],
        expected_completion_result=CompletenessResult.PASS,
        expected_release_decision=QualityReleaseDecision.RELEASE_READY,
        required_gate_refs=["058", "059", "060", "061", "062", "063"],
    )

    assert manifest.thresholds.required_quality_gate_count == 6
