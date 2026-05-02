"""Core operational observability gate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    AlertStatus,
    CompletenessResult,
    ObservabilityFailureType,
    ObservabilityMetricKind,
    ObservabilitySignalType,
    OpsFailureType,
    OpsRecoveryStatus,
    OpsSeverity,
    RecoveryActionType,
    RunbookActionStatus,
    TraceSpanKind,
    TraceSpanStatus,
)
from veracrawl.contracts.ops import (
    AlertRecord,
    FailureRecord,
    MetricSample,
    ObservabilityReport,
    ObservabilitySignal,
    RecoveryAction,
    RunbookAction,
    TraceSpan,
)


@dataclass(frozen=True)
class OperationalObservabilityGateResult:
    report: ObservabilityReport
    signals: list[ObservabilitySignal]
    metric_samples: list[MetricSample]
    trace_spans: list[TraceSpan]
    alert_records: list[AlertRecord]
    runbook_actions: list[RunbookAction]
    failure_records: list[FailureRecord]
    recovery_actions: list[RecoveryAction]


_FAILURES: dict[
    str,
    tuple[ObservabilityFailureType, str, RecoveryActionType],
] = {
    "observability-missing-metrics": (
        ObservabilityFailureType.MISSING_METRIC_REFS,
        "metric_sample_refs",
        RecoveryActionType.RESTORE_OBSERVABILITY_SIGNAL,
    ),
    "observability-missing-traces": (
        ObservabilityFailureType.MISSING_TRACE_REFS,
        "trace_span_refs",
        RecoveryActionType.RESTORE_OBSERVABILITY_SIGNAL,
    ),
    "observability-missing-alerts": (
        ObservabilityFailureType.MISSING_ALERT_REFS,
        "alert_record_refs",
        RecoveryActionType.RUN_OBSERVABILITY_RUNBOOK,
    ),
    "observability-missing-runbook": (
        ObservabilityFailureType.MISSING_RUNBOOK_REFS,
        "runbook_action_refs",
        RecoveryActionType.RUN_OBSERVABILITY_RUNBOOK,
    ),
    "observability-stale-dashboard-watermark": (
        ObservabilityFailureType.STALE_DASHBOARD_WATERMARK,
        "projection_watermark_refs",
        RecoveryActionType.REFRESH_DASHBOARD_PROJECTION,
    ),
    "observability-missing-dr-refs": (
        ObservabilityFailureType.MISSING_DR_REFS,
        "dr_restore_report_refs",
        RecoveryActionType.RESTORE_OBSERVABILITY_SIGNAL,
    ),
    "observability-missing-redaction": (
        ObservabilityFailureType.MISSING_REDACTION_REFS,
        "redaction_map_refs",
        RecoveryActionType.REDACT_SENSITIVE_CONTEXT,
    ),
    "observability-missing-replay": (
        ObservabilityFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_ref",
        RecoveryActionType.RESTORE_OBSERVABILITY_SIGNAL,
    ),
    "observability-secret-leak": (
        ObservabilityFailureType.SECRET_LEAK_DETECTED,
        "unredacted_sensitive_fields",
        RecoveryActionType.REDACT_SENSITIVE_CONTEXT,
    ),
    "observability-unsafe-runbook-without-approval": (
        ObservabilityFailureType.UNSAFE_RUNBOOK_WITHOUT_APPROVAL,
        "approval_decision_refs",
        RecoveryActionType.REQUEST_REVIEW,
    ),
}


def run_operational_observability_gate(
    *,
    fixture_id: str,
    scenario: str,
    telemetry_backend_ref: Ref | None,
    collector_handoff_ref: Ref | None,
) -> OperationalObservabilityGateResult:
    if scenario == "observability-runtime-unavailable":
        return run_operational_observability_runtime_unavailable_gate(fixture_id=fixture_id)
    if scenario == "observability-data-surface-only":
        return run_operational_observability_data_surface_only_gate(fixture_id=fixture_id)
    if scenario in _FAILURES:
        failure, missing_field, action_type = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            failure=failure,
            missing_field=missing_field,
            action_type=action_type,
        )
    if telemetry_backend_ref is None or collector_handoff_ref is None:
        return run_operational_observability_runtime_unavailable_gate(fixture_id=fixture_id)
    return _success_result(
        fixture_id=fixture_id,
        telemetry_backend_ref=telemetry_backend_ref,
        collector_handoff_ref=collector_handoff_ref,
    )


def run_operational_observability_runtime_unavailable_gate(
    *,
    fixture_id: str,
) -> OperationalObservabilityGateResult:
    report = ObservabilityReport(
        id=f"observability-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        contract_only_refs=[
            "telemetry-runtime:collector-required",
            "telemetry-runtime:backend-required",
            "telemetry-runtime:operational-handoff-not-executed",
        ],
        missing_ref_fields=["collector_handoff_refs", "telemetry_backend_refs"],
        operator_status="observability_runtime_unavailable",
        result=CompletenessResult.NEEDS_REVIEW,
    )
    return OperationalObservabilityGateResult(
        report=report,
        signals=[],
        metric_samples=[],
        trace_spans=[],
        alert_records=[],
        runbook_actions=[],
        failure_records=[],
        recovery_actions=[],
    )


def run_operational_observability_data_surface_only_gate(
    *,
    fixture_id: str,
) -> OperationalObservabilityGateResult:
    report = ObservabilityReport(
        id=f"observability-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        quality_report_refs=[f"quality-report:{fixture_id}"],
        dashboard_snapshot_refs=[f"ops-dashboard-snapshot:{fixture_id}"],
        projection_watermark_refs=[f"projection-watermark:{fixture_id}:ops"],
        policy_decision_refs=[f"policy:{fixture_id}:ops-console"],
        command_record_refs=[f"command:{fixture_id}:ops-console"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:ops-console"],
        outbox_refs=[f"outbox:{fixture_id}:ops-console"],
        redaction_map_refs=[f"redaction-map:{fixture_id}:ops-console"],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:ops-console",
        contract_only_refs=["ops-console:data-surface-only"],
        missing_ref_fields=[
            "signal_refs",
            "metric_sample_refs",
            "trace_span_refs",
            "alert_record_refs",
            "runbook_action_refs",
            "collector_handoff_refs",
            "telemetry_backend_refs",
        ],
        operator_status="observability_data_surface_only",
        result=CompletenessResult.NEEDS_REVIEW,
    )
    return OperationalObservabilityGateResult(
        report=report,
        signals=[],
        metric_samples=[],
        trace_spans=[],
        alert_records=[],
        runbook_actions=[],
        failure_records=[],
        recovery_actions=[],
    )


def _success_result(
    *,
    fixture_id: str,
    telemetry_backend_ref: Ref,
    collector_handoff_ref: Ref,
) -> OperationalObservabilityGateResult:
    policy_refs = [f"policy:{fixture_id}:observability"]
    approval_refs = [f"approval:{fixture_id}:runbook"]
    redaction_refs = [f"redaction-map:{fixture_id}:observability"]
    replay_ref = f"replay-bundle:{fixture_id}:observability"
    command_ref = f"command:{fixture_id}:observability"
    event_ref = f"event-cursor:{fixture_id}:observability"
    outbox_ref = f"outbox:{fixture_id}:observability"
    failure_record = _failure_record(
        fixture_id,
        failure=ObservabilityFailureType.STALE_DASHBOARD_WATERMARK,
        failed_ref=f"projection-watermark:{fixture_id}:quality-lag",
        policy_decision_refs=policy_refs,
    )
    recovery_action = _recovery_action(
        fixture_id,
        failure_record_id=failure_record.id,
        action_type=RecoveryActionType.REFRESH_DASHBOARD_PROJECTION,
        policy_decision_refs=policy_refs,
        approval_decision_refs=approval_refs,
    )
    trace_spans = [
        TraceSpan(
            id=f"trace-span:{fixture_id}:command",
            span_name="record_observability_report",
            span_kind=TraceSpanKind.COMMAND,
            run_ref=f"run:{fixture_id}",
            command_ref=command_ref,
            owner_service_ref="ops:observability",
            status=TraceSpanStatus.OK,
            duration_ms=32,
            redacted_attribute_refs=[f"trace-attrs-redacted:{fixture_id}:command"],
            policy_decision_refs=policy_refs,
        ),
        TraceSpan(
            id=f"trace-span:{fixture_id}:event",
            span_name="observability_reported",
            span_kind=TraceSpanKind.EVENT,
            run_ref=f"run:{fixture_id}",
            parent_span_ref=f"trace-span:{fixture_id}:command",
            event_ref=event_ref,
            owner_service_ref="runtime_events:observability",
            status=TraceSpanStatus.OK,
            duration_ms=7,
            redacted_attribute_refs=[f"trace-attrs-redacted:{fixture_id}:event"],
            policy_decision_refs=policy_refs,
        ),
    ]
    metric_samples = [
        MetricSample(
            id=f"metric-sample:{fixture_id}:projection-lag",
            metric_name="projection_lag_seconds",
            metric_kind=ObservabilityMetricKind.SLO,
            value=12.0,
            unit="seconds",
            run_ref=f"run:{fixture_id}",
            owner_service_ref="ops:observability",
            timestamp_ref=f"timestamp:{fixture_id}:metric",
            threshold_ref=f"threshold:{fixture_id}:projection-lag",
            policy_decision_refs=policy_refs,
            trace_refs=[span.id for span in trace_spans],
        ),
        MetricSample(
            id=f"metric-sample:{fixture_id}:token-spend",
            metric_name="token_spend_usd",
            metric_kind=ObservabilityMetricKind.COST,
            value=0.42,
            unit="usd",
            run_ref=f"run:{fixture_id}",
            owner_service_ref="ops:observability",
            timestamp_ref=f"timestamp:{fixture_id}:cost",
            threshold_ref=f"threshold:{fixture_id}:token-spend",
            policy_decision_refs=policy_refs,
            trace_refs=[trace_spans[0].id],
        ),
    ]
    runbook_actions = [
        RunbookAction(
            id=f"runbook-action:{fixture_id}:refresh-dashboard",
            action_type="refresh_dashboard_projection",
            status=RunbookActionStatus.EXECUTED,
            run_ref=f"run:{fixture_id}",
            alert_ref=f"alert:{fixture_id}:projection-lag",
            failure_record_refs=[failure_record.id],
            recovery_action_refs=[recovery_action.id],
            dr_restore_report_refs=[f"dr-restore-report:{fixture_id}"],
            side_effecting=True,
            approval_decision_refs=approval_refs,
            policy_decision_refs=policy_refs,
            command_refs=[command_ref],
            event_refs=[event_ref],
            replay_bundle_ref=replay_ref,
        )
    ]
    alert_records = [
        AlertRecord(
            id=f"alert:{fixture_id}:projection-lag",
            alert_type="recovery_projection_lag",
            severity=OpsSeverity.HIGH,
            status=AlertStatus.FIRING,
            run_ref=f"run:{fixture_id}",
            metric_refs=[sample.id for sample in metric_samples],
            trace_refs=[span.id for span in trace_spans],
            failure_record_refs=[failure_record.id],
            dr_restore_report_refs=[f"dr-restore-report:{fixture_id}"],
            runbook_action_refs=[runbook_actions[0].id],
            policy_decision_refs=policy_refs,
            replay_bundle_ref=replay_ref,
        )
    ]
    signals = [
        ObservabilitySignal(
            id=f"observability-signal:{fixture_id}:ops",
            signal_type=ObservabilitySignalType.RECOVERY,
            owner_service_ref="ops:observability",
            severity=OpsSeverity.HIGH,
            run_ref=f"run:{fixture_id}",
            source_ref=f"ops-console-report:{fixture_id}",
            metric_refs=[sample.id for sample in metric_samples],
            trace_refs=[span.id for span in trace_spans],
            alert_refs=[record.id for record in alert_records],
            policy_decision_refs=policy_refs,
            redaction_map_refs=redaction_refs,
            replay_bundle_ref=replay_ref,
            payload_refs=[f"observability-payload-redacted:{fixture_id}:ops"],
        )
    ]
    report = ObservabilityReport(
        id=f"observability-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        signal_refs=[signal.id for signal in signals],
        metric_sample_refs=[sample.id for sample in metric_samples],
        trace_span_refs=[span.id for span in trace_spans],
        alert_record_refs=[record.id for record in alert_records],
        runbook_action_refs=[action.id for action in runbook_actions],
        quality_report_refs=[f"quality-report:{fixture_id}"],
        cost_metric_refs=[metric_samples[1].id],
        dashboard_snapshot_refs=[f"ops-dashboard-snapshot:{fixture_id}"],
        projection_watermark_refs=[f"projection-watermark:{fixture_id}:quality"],
        failure_record_refs=[failure_record.id],
        recovery_action_refs=[recovery_action.id],
        dr_restore_report_refs=[f"dr-restore-report:{fixture_id}"],
        policy_decision_refs=policy_refs,
        command_record_refs=[command_ref],
        event_cursor_refs=[event_ref],
        outbox_refs=[outbox_ref],
        redaction_map_refs=redaction_refs,
        collector_handoff_refs=[collector_handoff_ref],
        telemetry_backend_refs=[telemetry_backend_ref],
        replay_bundle_ref=replay_ref,
        operator_status="operational_observability_completed",
        result=CompletenessResult.PASS,
    )
    return OperationalObservabilityGateResult(
        report=report,
        signals=signals,
        metric_samples=metric_samples,
        trace_spans=trace_spans,
        alert_records=alert_records,
        runbook_actions=runbook_actions,
        failure_records=[failure_record],
        recovery_actions=[recovery_action],
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: ObservabilityFailureType,
    missing_field: str,
    action_type: RecoveryActionType,
) -> OperationalObservabilityGateResult:
    policy_refs = [f"policy:{fixture_id}:observability"]
    approval_refs = [f"approval:{fixture_id}:observability"]
    failure_record = _failure_record(
        fixture_id,
        failure=failure,
        failed_ref=f"observability-report:{fixture_id}",
        policy_decision_refs=policy_refs,
    )
    recovery_action = _recovery_action(
        fixture_id,
        failure_record_id=failure_record.id,
        action_type=action_type,
        policy_decision_refs=policy_refs,
        approval_decision_refs=approval_refs,
    )
    report = ObservabilityReport(
        id=f"observability-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        signal_refs=[]
        if missing_field == "signal_refs"
        else [f"observability-signal:{fixture_id}:ops"],
        metric_sample_refs=[]
        if missing_field == "metric_sample_refs"
        else [f"metric-sample:{fixture_id}:projection-lag"],
        trace_span_refs=[]
        if missing_field == "trace_span_refs"
        else [f"trace-span:{fixture_id}:command"],
        alert_record_refs=[]
        if missing_field == "alert_record_refs"
        else [f"alert:{fixture_id}:projection-lag"],
        runbook_action_refs=[]
        if missing_field == "runbook_action_refs"
        else [f"runbook-action:{fixture_id}:refresh-dashboard"],
        quality_report_refs=[f"quality-report:{fixture_id}"],
        cost_metric_refs=[f"metric-sample:{fixture_id}:token-spend"],
        dashboard_snapshot_refs=[f"ops-dashboard-snapshot:{fixture_id}"],
        projection_watermark_refs=[]
        if missing_field == "projection_watermark_refs"
        else [f"projection-watermark:{fixture_id}:quality"],
        failure_record_refs=[failure_record.id],
        recovery_action_refs=[recovery_action.id],
        dr_restore_report_refs=[]
        if missing_field == "dr_restore_report_refs"
        else [f"dr-restore-report:{fixture_id}"],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command:{fixture_id}:observability"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:observability"],
        outbox_refs=[f"outbox:{fixture_id}:observability"],
        redaction_map_refs=[]
        if missing_field == "redaction_map_refs"
        else [f"redaction-map:{fixture_id}:observability"],
        collector_handoff_refs=[f"collector-handoff:{fixture_id}"],
        telemetry_backend_refs=[f"telemetry-backend:{fixture_id}"],
        replay_bundle_ref=None
        if missing_field == "replay_bundle_ref"
        else f"replay-bundle:{fixture_id}:observability",
        missing_ref_fields=[missing_field],
        stale_projection_refs=[f"projection-watermark:{fixture_id}:stale"]
        if missing_field == "projection_watermark_refs"
        else [],
        unredacted_sensitive_fields=["trace_span.attributes.raw_secret"]
        if missing_field == "unredacted_sensitive_fields"
        else [],
        unsafe_runbook_action_refs=[f"runbook-action:{fixture_id}:unsafe"]
        if missing_field == "approval_decision_refs"
        else [],
        operator_status=failure.value,
        result=CompletenessResult.FAIL,
    )
    return OperationalObservabilityGateResult(
        report=report,
        signals=[],
        metric_samples=[],
        trace_spans=[],
        alert_records=[],
        runbook_actions=[],
        failure_records=[failure_record],
        recovery_actions=[recovery_action],
    )


def _failure_record(
    fixture_id: str,
    *,
    failure: ObservabilityFailureType,
    failed_ref: Ref,
    policy_decision_refs: list[Ref],
) -> FailureRecord:
    failure_type = _ops_failure_type_for(failure)
    return FailureRecord(
        id=f"failure-record:{fixture_id}:{failure.value}",
        run_id=f"run:{fixture_id}",
        failure_type=failure_type,
        failed_ref=failed_ref,
        owner_service_ref="ops:observability",
        severity=OpsSeverity.HIGH,
        retryable=True,
        diagnostic_ref=f"diagnostic:{fixture_id}:{failure.value}",
        policy_decision_refs=policy_decision_refs,
        replay_audit_refs=[f"replay-audit:{fixture_id}:observability"],
    )


def _recovery_action(
    fixture_id: str,
    *,
    failure_record_id: str,
    action_type: RecoveryActionType,
    policy_decision_refs: list[Ref],
    approval_decision_refs: list[Ref],
) -> RecoveryAction:
    return RecoveryAction(
        id=f"recovery-action:{fixture_id}:{action_type.value}",
        failure_record_id=failure_record_id,
        action_type=action_type,
        command_refs=[f"command:{fixture_id}:{action_type.value}"]
        if action_type != RecoveryActionType.REQUEST_REVIEW
        else [],
        policy_decision_refs=policy_decision_refs,
        approval_decision_refs=approval_decision_refs
        if action_type != RecoveryActionType.REQUEST_REVIEW
        else [],
        review_item_refs=[f"review-item:{fixture_id}:observability"],
        status=OpsRecoveryStatus.PROPOSED,
    )


def _ops_failure_type_for(failure: ObservabilityFailureType) -> OpsFailureType:
    if failure == ObservabilityFailureType.SECRET_LEAK_DETECTED:
        return OpsFailureType.REDACTION_VIOLATION
    if failure == ObservabilityFailureType.UNSAFE_RUNBOOK_WITHOUT_APPROVAL:
        return OpsFailureType.UNSAFE_RECOVERY_WITHOUT_REVIEW
    if failure == ObservabilityFailureType.STALE_DASHBOARD_WATERMARK:
        return OpsFailureType.STALE_DASHBOARD_PROJECTION
    return OpsFailureType.OBSERVABILITY_GAP
