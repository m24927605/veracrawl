"""Deterministic ops replay and observability runtime aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    OpsReplayObservabilityFailureType,
)
from veracrawl.contracts.ops import OpsReplayObservabilityRuntimeReport
from veracrawl.evidence.live_verification import run_live_evidence_verification_runtime
from veracrawl.extract.schema_runtime import run_schema_extraction_runtime
from veracrawl.normalize.pipeline import NormalizationResult, normalize_html_document
from veracrawl.ops.console import OpsConsoleResult, run_ops_console
from veracrawl.publish.result_runtime import (
    ResultPublicationExportRuntimeResult,
    run_result_publication_export_runtime,
)
from veracrawl.runtime_support.observability import (
    OperationalObservabilityGateResult,
    run_operational_observability_gate,
)
from veracrawl.scale.worker_orchestration import (
    WorkerOrchestrationRuntimeResult,
    run_worker_orchestration_runtime,
)


@dataclass(frozen=True)
class OpsReplayObservabilityRuntimeResult:
    report: OpsReplayObservabilityRuntimeReport
    publication: ResultPublicationExportRuntimeResult | None = None
    worker_orchestration: WorkerOrchestrationRuntimeResult | None = None
    ops_console: OpsConsoleResult | None = None
    observability: OperationalObservabilityGateResult | None = None


@dataclass(frozen=True)
class _RuntimeDependencies:
    publication: ResultPublicationExportRuntimeResult | None
    worker: WorkerOrchestrationRuntimeResult | None
    ops: OpsConsoleResult | None
    observability: OperationalObservabilityGateResult | None


_DEPENDENCY_FAILURES: dict[
    str,
    tuple[OpsReplayObservabilityFailureType, str],
] = {
    "ops-runtime-missing-publication": (
        OpsReplayObservabilityFailureType.MISSING_PUBLICATION,
        "result_publication_export_report_ref",
    ),
    "ops-runtime-missing-worker-orchestration": (
        OpsReplayObservabilityFailureType.MISSING_WORKER_ORCHESTRATION,
        "worker_orchestration_runtime_report_ref",
    ),
    "ops-runtime-missing-ops-console": (
        OpsReplayObservabilityFailureType.MISSING_OPS_CONSOLE,
        "ops_console_report_ref",
    ),
    "ops-runtime-missing-observability": (
        OpsReplayObservabilityFailureType.MISSING_OBSERVABILITY,
        "observability_report_ref",
    ),
}


def run_ops_replay_observability_runtime(
    *,
    fixture_id: str,
    scenario: str,
    telemetry_backend_ref: Ref | None = None,
    collector_handoff_ref: Ref | None = None,
) -> OpsReplayObservabilityRuntimeResult:
    backend_ref = telemetry_backend_ref or f"telemetry-backend:{fixture_id}:ops-runtime"
    handoff_ref = collector_handoff_ref or f"collector-handoff:{fixture_id}:ops-runtime"

    if scenario in _DEPENDENCY_FAILURES:
        failure, missing_field = _DEPENDENCY_FAILURES[scenario]
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            include_publication=failure
            != OpsReplayObservabilityFailureType.MISSING_PUBLICATION,
            include_worker=failure
            != OpsReplayObservabilityFailureType.MISSING_WORKER_ORCHESTRATION,
            include_ops=failure != OpsReplayObservabilityFailureType.MISSING_OPS_CONSOLE,
            include_observability=failure
            != OpsReplayObservabilityFailureType.MISSING_OBSERVABILITY,
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=failure,
            missing_ref_fields=[missing_field],
        )

    if scenario == "ops-runtime-stale-dashboard":
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            ops_scenario="stale-dashboard-projection",
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=OpsReplayObservabilityFailureType.STALE_DASHBOARD,
            missing_ref_fields=["dashboard_snapshot_refs"],
            stale_dashboard_refs=[f"ops-dashboard-snapshot:{fixture_id}:stale"],
        )

    if scenario == "ops-runtime-unresolved-recovery":
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            ops_scenario="unresolved-failure-without-recovery",
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=OpsReplayObservabilityFailureType.UNRESOLVED_RECOVERY,
            missing_ref_fields=["recovery_action_refs"],
            unresolved_recovery_refs=[f"failure-record:{fixture_id}:unresolved"],
        )

    if scenario == "ops-runtime-unsafe-operator-action":
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            ops_scenario="unsafe-recovery-without-review",
            observability_scenario="observability-unsafe-runbook-without-approval",
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=OpsReplayObservabilityFailureType.UNSAFE_OPERATOR_ACTION,
            missing_ref_fields=["approval_decision_refs"],
            unsafe_operator_action_refs=[f"operator-action:{fixture_id}:unsafe"],
        )

    if scenario == "ops-runtime-replay-mismatch":
        deps = _collect_dependencies(
            fixture_id=fixture_id,
            telemetry_backend_ref=backend_ref,
            collector_handoff_ref=handoff_ref,
        )
        return _failure_result(
            fixture_id=fixture_id,
            deps=deps,
            failure=OpsReplayObservabilityFailureType.REPLAY_MISMATCH,
            missing_ref_fields=["replay_bundle_ref"],
            replay_gap_refs=[f"replay-gap:{fixture_id}:ops-runtime"],
        )

    deps = _collect_dependencies(
        fixture_id=fixture_id,
        telemetry_backend_ref=backend_ref,
        collector_handoff_ref=handoff_ref,
    )
    return OpsReplayObservabilityRuntimeResult(
        report=_pass_report(
            fixture_id=fixture_id,
            scenario=scenario,
            deps=deps,
        ),
        publication=deps.publication,
        worker_orchestration=deps.worker,
        ops_console=deps.ops,
        observability=deps.observability,
    )


def _collect_dependencies(
    *,
    fixture_id: str,
    include_publication: bool = True,
    include_worker: bool = True,
    include_ops: bool = True,
    include_observability: bool = True,
    ops_scenario: str = "review-console-success",
    observability_scenario: str = "observability-success",
    telemetry_backend_ref: Ref,
    collector_handoff_ref: Ref,
) -> _RuntimeDependencies:
    publication = _run_result_publication(fixture_id) if include_publication else None
    worker = (
        run_worker_orchestration_runtime(
            fixture_id=fixture_id,
            scenario="worker-orchestration-production-success",
        )
        if include_worker
        else None
    )
    ops = (
        run_ops_console(
            fixture_id=fixture_id,
            scenario=ops_scenario,
            policy_decision_refs=[f"policy:{fixture_id}:ops-runtime"],
        )
        if include_ops
        else None
    )
    observability = (
        run_operational_observability_gate(
            fixture_id=fixture_id,
            scenario=observability_scenario,
            telemetry_backend_ref=telemetry_backend_ref,
            collector_handoff_ref=collector_handoff_ref,
        )
        if include_observability
        else None
    )
    return _RuntimeDependencies(
        publication=publication,
        worker=worker,
        ops=ops,
        observability=observability,
    )


def _run_result_publication(fixture_id: str) -> ResultPublicationExportRuntimeResult:
    normalization = _normalization(fixture_id)
    schema_result = run_schema_extraction_runtime(
        fixture_id=f"{fixture_id}-schema-extraction",
        scenario="schema-extraction-record-success",
        live_normalization_runtime_report_ref=f"live-normalization-runtime-report:{fixture_id}",
        normalization=normalization,
        schema_ref="schema:record-summary",
    )
    if schema_result.candidate is None:
        raise ValueError("schema extraction must produce candidate for ops runtime")
    live_evidence = run_live_evidence_verification_runtime(
        fixture_id=f"{fixture_id}-live-evidence",
        scenario="live-evidence-verification-success",
        schema_extraction_runtime_report_ref=schema_result.report.id,
        candidate=schema_result.candidate,
        normalized_document_ref=normalization.normalized_document.id,
        source_artifact_ref=normalization.normalized_document.raw_artifact_ref,
        source_anchor_refs=schema_result.report.source_anchor_refs,
    )
    if (
        live_evidence.evidence is None
        or live_evidence.verification is None
        or live_evidence.review is None
    ):
        raise ValueError("live evidence must produce evidence, verification, and review")
    return run_result_publication_export_runtime(
        fixture_id=fixture_id,
        scenario="result-publication-export-success",
        live_evidence_runtime_report_ref=live_evidence.report.id,
        candidate=schema_result.candidate,
        evidence=live_evidence.evidence,
        verification=live_evidence.verification,
        review=live_evidence.review,
    )


def _normalization(fixture_id: str) -> NormalizationResult:
    return normalize_html_document(
        fixture_id=f"{fixture_id}-live-normalization",
        run_ref=f"run:{fixture_id}-live-normalization",
        source_adapter_result_ref=f"source-result:{fixture_id}",
        source_url="http://example.test/static/basic",
        raw_artifact_ref=f"artifact:{fixture_id}:raw",
        raw_html=(
            "<!doctype html><html><title>Vera</title><body><main><h1>Static fixture</h1>"
            "<a href='/static/detail'>Detail</a></main></body></html>"
        ),
        policy_decision_refs=[f"policy:{fixture_id}:live-normalization"],
    )


def _pass_report(
    *,
    fixture_id: str,
    scenario: str,
    deps: _RuntimeDependencies,
) -> OpsReplayObservabilityRuntimeReport:
    if not (deps.publication and deps.worker and deps.ops and deps.observability):
        raise ValueError("passing ops runtime requires all dependencies")
    publication_report = deps.publication.report
    worker_report = deps.worker.report
    ops_report = deps.ops.report
    observability_report = deps.observability.report
    dashboard_refs = _present([ops_report.dashboard_snapshot_ref])
    dashboard_refs.extend(observability_report.dashboard_snapshot_refs)
    return OpsReplayObservabilityRuntimeReport(
        id=f"ops-replay-observability-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        result_publication_export_report_ref=publication_report.id,
        worker_orchestration_runtime_report_ref=worker_report.id,
        ops_console_report_ref=ops_report.id,
        observability_report_ref=observability_report.id,
        run_control_action_refs=[
            f"run-control-action:{fixture_id}:pause",
            f"run-control-action:{fixture_id}:resume",
        ],
        review_item_refs=ops_report.review_item_refs,
        evidence_review_refs=publication_report.review_decision_refs,
        replay_audit_view_refs=ops_report.replay_audit_view_refs,
        graph_debug_refs=[
            f"graph-debug:{fixture_id}:frontier",
            f"graph-debug:{fixture_id}:evidence-lineage",
        ],
        export_status_refs=[
            *publication_report.export_job_refs,
            *publication_report.export_attempt_refs,
            *publication_report.delivery_receipt_refs,
        ],
        withdrawal_status_refs=[
            *publication_report.withdrawal_job_refs,
            *publication_report.withdrawal_attempt_refs,
            *publication_report.correction_record_refs,
            *publication_report.destination_object_mapping_refs,
        ],
        recovery_action_refs=[
            *ops_report.recovery_action_refs,
            *observability_report.recovery_action_refs,
            *worker_report.recovery_action_refs,
        ],
        failure_record_refs=[
            *ops_report.failure_record_refs,
            *observability_report.failure_record_refs,
            *worker_report.failure_record_refs,
        ],
        dr_restore_report_refs=[
            *ops_report.dr_restore_report_refs,
            *observability_report.dr_restore_report_refs,
        ],
        quality_report_refs=[
            *ops_report.quality_report_refs,
            *observability_report.quality_report_refs,
        ],
        dashboard_snapshot_refs=dashboard_refs,
        alert_record_refs=observability_report.alert_record_refs,
        runbook_action_refs=observability_report.runbook_action_refs,
        cost_metric_refs=observability_report.cost_metric_refs,
        observability_signal_refs=observability_report.signal_refs,
        metric_sample_refs=observability_report.metric_sample_refs,
        trace_span_refs=observability_report.trace_span_refs,
        policy_decision_refs=_dedupe(
            [
                *publication_report.policy_decision_refs,
                *worker_report.policy_decision_refs,
                *ops_report.policy_decision_refs,
                *observability_report.policy_decision_refs,
                f"policy:{fixture_id}:operator-action",
            ]
        ),
        command_record_refs=_dedupe(
            [
                *publication_report.command_record_refs,
                *worker_report.command_record_refs,
                *ops_report.command_record_refs,
                *observability_report.command_record_refs,
            ]
        ),
        event_cursor_refs=_dedupe(
            [
                *publication_report.event_cursor_refs,
                *worker_report.event_cursor_refs,
                *ops_report.event_cursor_refs,
                *observability_report.event_cursor_refs,
            ]
        ),
        outbox_refs=_dedupe(
            [
                *publication_report.outbox_refs,
                *worker_report.outbox_refs,
                *ops_report.outbox_refs,
                *observability_report.outbox_refs,
            ]
        ),
        redaction_map_refs=[
            *observability_report.redaction_map_refs,
            f"redaction-map:{fixture_id}:operator-console",
        ],
        replay_bundle_ref=f"replay-bundle:{fixture_id}:ops-runtime",
        operator_status=_operator_status(scenario),
        completion_result=CompletenessResult.PASS,
    )


def _failure_result(
    *,
    fixture_id: str,
    deps: _RuntimeDependencies,
    failure: OpsReplayObservabilityFailureType,
    missing_ref_fields: list[str] | None = None,
    stale_dashboard_refs: list[Ref] | None = None,
    unresolved_recovery_refs: list[Ref] | None = None,
    unsafe_operator_action_refs: list[Ref] | None = None,
    observability_gap_refs: list[Ref] | None = None,
    replay_gap_refs: list[Ref] | None = None,
) -> OpsReplayObservabilityRuntimeResult:
    publication_report = deps.publication.report if deps.publication else None
    worker_report = deps.worker.report if deps.worker else None
    ops_report = deps.ops.report if deps.ops else None
    observability_report = deps.observability.report if deps.observability else None
    replay_mismatch = failure == OpsReplayObservabilityFailureType.REPLAY_MISMATCH
    command_record_refs = [] if replay_mismatch else [f"command-record:{fixture_id}:ops-runtime"]
    event_cursor_refs = [] if replay_mismatch else [f"event-cursor:{fixture_id}:ops-runtime"]
    outbox_refs = [] if replay_mismatch else [f"outbox:{fixture_id}:ops-runtime"]
    report = OpsReplayObservabilityRuntimeReport(
        id=f"ops-replay-observability-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=f"run:{fixture_id}",
        result_publication_export_report_ref=publication_report.id
        if publication_report
        else None,
        worker_orchestration_runtime_report_ref=worker_report.id
        if worker_report
        else None,
        ops_console_report_ref=ops_report.id if ops_report else None,
        observability_report_ref=observability_report.id if observability_report else None,
        policy_decision_refs=[f"policy:{fixture_id}:ops-runtime"],
        command_record_refs=command_record_refs,
        event_cursor_refs=event_cursor_refs,
        outbox_refs=outbox_refs,
        failure_type=failure,
        failure_report_refs=[f"failure-report:{fixture_id}:{failure.value}"],
        missing_ref_fields=missing_ref_fields or [failure.value],
        stale_dashboard_refs=stale_dashboard_refs or [],
        unresolved_recovery_refs=unresolved_recovery_refs or [],
        unsafe_operator_action_refs=unsafe_operator_action_refs or [],
        observability_gap_refs=observability_gap_refs
        or (
            [f"observability-report:{fixture_id}:missing"]
            if failure == OpsReplayObservabilityFailureType.MISSING_OBSERVABILITY
            else []
        ),
        replay_gap_refs=replay_gap_refs or [],
        diagnostics=[failure.value],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )
    return OpsReplayObservabilityRuntimeResult(
        report=report,
        publication=deps.publication,
        worker_orchestration=deps.worker,
        ops_console=deps.ops,
        observability=deps.observability,
    )


def _operator_status(scenario: str) -> str:
    if scenario == "ops-runtime-incident-recovery-success":
        return "ops_replay_observability_incident_recovered"
    if scenario == "ops-runtime-cost-alert-success":
        return "ops_replay_observability_cost_alert_completed"
    return "ops_replay_observability_completed"


def _present(values: list[Ref | None]) -> list[Ref]:
    return [value for value in values if value]


def _dedupe(values: list[Ref]) -> list[Ref]:
    return list(dict.fromkeys(values))
