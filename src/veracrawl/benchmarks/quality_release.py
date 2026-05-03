"""Cost, latency, stability quality release gate runtime."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    QualityReleaseDecision,
    QualityReleaseFailureType,
    QualityReleaseGateType,
)
from veracrawl.contracts.quality_release import (
    QualityReleaseGateRef,
    QualityReleaseManifest,
    QualityReleaseReport,
    QualityReleaseStabilityRun,
)
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.control.runtime import create_runtime_command


@dataclass(frozen=True)
class QualityReleaseGateResult:
    report: QualityReleaseReport
    quality_gates: list[QualityReleaseGateRef]
    stability_runs: list[QualityReleaseStabilityRun]


_DIRECT_FAILURES: dict[str, tuple[QualityReleaseFailureType, str]] = {
    "quality-release-missing-prior-gate": (
        QualityReleaseFailureType.MISSING_QUALITY_GATE_REPORT,
        "quality_gate_refs",
    ),
    "quality-release-cost-exceeded": (
        QualityReleaseFailureType.COST_BUDGET_EXCEEDED,
        "total_cost_usd",
    ),
    "quality-release-latency-violation": (
        QualityReleaseFailureType.LATENCY_SLO_VIOLATION,
        "p95_latency_ms",
    ),
    "quality-release-retry-violation": (
        QualityReleaseFailureType.RETRY_RATE_EXCEEDED,
        "retry_rate",
    ),
    "quality-release-stability-regression": (
        QualityReleaseFailureType.STABILITY_REGRESSION,
        "stability_variance",
    ),
    "quality-release-insufficient-runs": (
        QualityReleaseFailureType.INSUFFICIENT_STABILITY_RUNS,
        "stability_run_refs",
    ),
    "quality-release-replay-gap": (
        QualityReleaseFailureType.REPLAY_GAP,
        "replay_bundle_refs",
    ),
    "quality-release-false-ready": (
        QualityReleaseFailureType.FALSE_READY_STATUS,
        "release_decision_refs",
    ),
    "quality-release-missing-command-event": (
        QualityReleaseFailureType.MISSING_COMMAND_EVENT_REFS,
        "command_record_refs",
    ),
}


def run_quality_release_gate(
    *,
    manifest: QualityReleaseManifest,
    profile: str,
    store: ProductionPersistenceStore,
) -> QualityReleaseGateResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"quality release fixture {manifest.id} does not support {profile}")

    quality_gates = _generate_quality_gate_refs(manifest.id)
    stability_runs = _generate_stability_runs(manifest.id)
    if manifest.scenario in _DIRECT_FAILURES:
        failure, missing = _DIRECT_FAILURES[manifest.scenario]
        report = _direct_failure_report(
            manifest,
            quality_gates,
            stability_runs,
            failure,
            missing,
        )
        store.save_canonical_model("quality_release_reports", report.id, report)
        return QualityReleaseGateResult(
            report=report,
            quality_gates=quality_gates,
            stability_runs=stability_runs,
        )

    quality_gates = [
        _record_gate_event(manifest.id, gate_ref, store) for gate_ref in quality_gates
    ]
    stability_runs = [
        _record_stability_event(manifest.id, stability_run, store)
        for stability_run in stability_runs
    ]
    report = _build_report(manifest, quality_gates, stability_runs)
    store.save_canonical_model("quality_release_reports", report.id, report)
    report = _record_report_event(manifest.id, report, store)
    store.save_canonical_model("quality_release_reports", report.id, report)
    return QualityReleaseGateResult(
        report=report,
        quality_gates=quality_gates,
        stability_runs=stability_runs,
    )


def _generate_quality_gate_refs(fixture_id: str) -> list[QualityReleaseGateRef]:
    gates = [
        (
            QualityReleaseGateType.REAL_WORLD_PUBLIC_CORPUS,
            "real-world-quality-corpus-report",
        ),
        (QualityReleaseGateType.BROWSER_QUALITY, "browser-quality-report"),
        (QualityReleaseGateType.DEEP_CRAWL_FRONTIER, "deep-crawl-quality-report"),
        (QualityReleaseGateType.FIELD_LEVEL_ORACLE, "field-oracle-report"),
        (QualityReleaseGateType.PRECISION_RECALL, "precision-recall-report"),
        (QualityReleaseGateType.REPAIR_SUCCESS, "repair-quality-report"),
    ]
    return [
        QualityReleaseGateRef(
            id=f"quality-release-gate-ref:{fixture_id}:{gate_type.value}",
            gate_type=gate_type,
            report_ref=f"{report_slug}:{fixture_id}",
            completion_result=CompletenessResult.PASS,
            replay_bundle_ref=f"replay-bundle:{fixture_id}:{gate_type.value}",
            policy_decision_refs=[f"policy:quality-release:{fixture_id}:{gate_type.value}"],
            command_record_refs=[f"command:quality-gate:{fixture_id}:{gate_type.value}"],
            event_cursor_refs=[
                f"event-cursor:quality-gate:{fixture_id}:{gate_type.value}"
            ],
            outbox_refs=[f"outbox:quality-gate:{fixture_id}:{gate_type.value}"],
        )
        for gate_type, report_slug in gates
    ]


def _generate_stability_runs(fixture_id: str) -> list[QualityReleaseStabilityRun]:
    return [
        QualityReleaseStabilityRun(
            id=f"quality-release-stability-run:{fixture_id}:{index}",
            run_ref=f"run:quality-release:{fixture_id}:{index}",
            total_cost_usd=0.42 + (index * 0.01),
            p95_latency_ms=3100 + (index * 80),
            throughput_pages_per_minute=44.0 - index,
            retry_rate=0.03 + (index * 0.005),
            token_count=39000 + (index * 750),
            model_call_count=81 + index,
            policy_decision_refs=[f"policy:quality-release:{fixture_id}:run:{index}"],
            command_record_refs=[f"command:quality-release-run:{fixture_id}:{index}"],
            event_cursor_refs=[f"event-cursor:quality-release-run:{fixture_id}:{index}"],
            outbox_refs=[f"outbox:quality-release-run:{fixture_id}:{index}"],
            slo_metric_refs=[f"slo-metric:quality-release:{fixture_id}:{index}"],
            replay_bundle_ref=f"replay-bundle:quality-release-run:{fixture_id}:{index}",
        )
        for index in range(1, 4)
    ]


def _record_gate_event(
    manifest_id: str,
    gate_ref: QualityReleaseGateRef,
    store: ProductionPersistenceStore,
) -> QualityReleaseGateRef:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{gate_ref.id}",
        command_type="record_quality_release_gate_ref",
        target_aggregate_type="QualityReleaseGateRef",
        target_aggregate_id=gate_ref.id,
        event_type="quality_release_gate_ref_recorded",
        output_refs=[gate_ref.id],
        policy_decision_refs=gate_ref.policy_decision_refs,
        store=store,
    )
    updated = gate_ref.model_copy(
        update={
            "command_record_refs": sorted(set(gate_ref.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(gate_ref.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(gate_ref.outbox_refs + [outbox_ref])),
        }
    )
    store.save_canonical_model("quality_release_gate_refs", updated.id, updated)
    return updated


def _record_stability_event(
    manifest_id: str,
    stability_run: QualityReleaseStabilityRun,
    store: ProductionPersistenceStore,
) -> QualityReleaseStabilityRun:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{stability_run.id}",
        command_type="record_quality_release_stability_run",
        target_aggregate_type="QualityReleaseStabilityRun",
        target_aggregate_id=stability_run.id,
        event_type="quality_release_stability_run_recorded",
        output_refs=[stability_run.id],
        policy_decision_refs=stability_run.policy_decision_refs,
        store=store,
    )
    updated = stability_run.model_copy(
        update={
            "command_record_refs": sorted(
                set(stability_run.command_record_refs + [command_ref])
            ),
            "event_cursor_refs": sorted(
                set(stability_run.event_cursor_refs + [event_ref])
            ),
            "outbox_refs": sorted(set(stability_run.outbox_refs + [outbox_ref])),
        }
    )
    store.save_canonical_model("quality_release_stability_runs", updated.id, updated)
    return updated


def _build_report(
    manifest: QualityReleaseManifest,
    quality_gates: list[QualityReleaseGateRef],
    stability_runs: list[QualityReleaseStabilityRun],
) -> QualityReleaseReport:
    total_cost = round(sum(item.total_cost_usd for item in stability_runs), 6)
    p95_latency = max(item.p95_latency_ms for item in stability_runs)
    throughput = min(item.throughput_pages_per_minute for item in stability_runs)
    retry_rate = max(item.retry_rate for item in stability_runs)
    token_count = sum(item.token_count for item in stability_runs)
    model_call_count = sum(item.model_call_count for item in stability_runs)
    stability_variance = _stability_variance(
        [item.throughput_pages_per_minute for item in stability_runs]
    )
    failure_type, diagnostics, missing = _threshold_failure(
        manifest,
        quality_gates=quality_gates,
        stability_runs=stability_runs,
        total_cost=total_cost,
        p95_latency=p95_latency,
        throughput=throughput,
        retry_rate=retry_rate,
        token_count=token_count,
        model_call_count=model_call_count,
        stability_variance=stability_variance,
    )
    passing = failure_type is None
    return QualityReleaseReport(
        id=f"quality-release-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        thresholds_ref=manifest.thresholds.id,
        quality_gate_refs=[item.id for item in quality_gates],
        stability_run_refs=[item.id for item in stability_runs],
        required_quality_gate_count=manifest.thresholds.required_quality_gate_count,
        observed_quality_gate_count=len(quality_gates),
        stability_run_count=len(stability_runs),
        total_cost_usd=total_cost,
        p95_latency_ms=p95_latency,
        throughput_pages_per_minute=throughput,
        retry_rate=retry_rate,
        token_count=token_count,
        model_call_count=model_call_count,
        stability_variance=stability_variance,
        gate_report_refs=[item.report_ref for item in quality_gates],
        policy_decision_refs=_collect("policy_decision_refs", quality_gates)
        + _collect("policy_decision_refs", stability_runs),
        command_record_refs=_collect("command_record_refs", quality_gates)
        + _collect("command_record_refs", stability_runs),
        event_cursor_refs=_collect("event_cursor_refs", quality_gates)
        + _collect("event_cursor_refs", stability_runs),
        outbox_refs=_collect("outbox_refs", quality_gates)
        + _collect("outbox_refs", stability_runs),
        slo_metric_refs=_collect("slo_metric_refs", stability_runs),
        audit_report_refs=[f"audit:quality-release:{manifest.id}"],
        release_decision_refs=[f"release-decision:quality-release:{manifest.id}"],
        replay_bundle_refs=_collect_one("replay_bundle_ref", quality_gates)
        + _collect_one("replay_bundle_ref", stability_runs),
        failure_report_refs=[f"failure:{manifest.id}:{failure_type.value}"]
        if failure_type
        else [],
        missing_ref_fields=missing,
        failure_type=failure_type,
        diagnostics=diagnostics,
        release_decision=(
            QualityReleaseDecision.RELEASE_READY
            if passing
            else QualityReleaseDecision.BLOCKED
        ),
        completion_result=CompletenessResult.PASS if passing else CompletenessResult.FAIL,
    )


def _threshold_failure(
    manifest: QualityReleaseManifest,
    *,
    quality_gates: list[QualityReleaseGateRef],
    stability_runs: list[QualityReleaseStabilityRun],
    total_cost: float,
    p95_latency: int,
    throughput: float,
    retry_rate: float,
    token_count: int,
    model_call_count: int,
    stability_variance: float,
) -> tuple[QualityReleaseFailureType | None, list[str], list[str]]:
    thresholds = manifest.thresholds
    if len(quality_gates) < thresholds.required_quality_gate_count:
        return (
            QualityReleaseFailureType.MISSING_QUALITY_GATE_REPORT,
            ["required prior quality gate report missing"],
            ["quality_gate_refs"],
        )
    if len(stability_runs) < thresholds.min_stability_run_count:
        return (
            QualityReleaseFailureType.INSUFFICIENT_STABILITY_RUNS,
            ["insufficient stability runs"],
            ["stability_run_refs"],
        )
    if total_cost > thresholds.max_total_cost_usd:
        return (
            QualityReleaseFailureType.COST_BUDGET_EXCEEDED,
            ["total cost exceeds threshold"],
            ["total_cost_usd"],
        )
    if p95_latency > thresholds.max_p95_latency_ms:
        return (
            QualityReleaseFailureType.LATENCY_SLO_VIOLATION,
            ["p95 latency exceeds threshold"],
            ["p95_latency_ms"],
        )
    if throughput < thresholds.min_throughput_pages_per_minute:
        return (
            QualityReleaseFailureType.STABILITY_REGRESSION,
            ["throughput below threshold"],
            ["throughput_pages_per_minute"],
        )
    if retry_rate > thresholds.max_retry_rate:
        return (
            QualityReleaseFailureType.RETRY_RATE_EXCEEDED,
            ["retry rate exceeds threshold"],
            ["retry_rate"],
        )
    if token_count > thresholds.max_token_count:
        return (
            QualityReleaseFailureType.COST_BUDGET_EXCEEDED,
            ["token count exceeds threshold"],
            ["token_count"],
        )
    if model_call_count > thresholds.max_model_call_count:
        return (
            QualityReleaseFailureType.COST_BUDGET_EXCEEDED,
            ["model call count exceeds threshold"],
            ["model_call_count"],
        )
    if stability_variance > thresholds.max_stability_variance:
        return (
            QualityReleaseFailureType.STABILITY_REGRESSION,
            ["stability variance exceeds threshold"],
            ["stability_variance"],
        )
    return None, [], []


def _direct_failure_report(
    manifest: QualityReleaseManifest,
    quality_gates: list[QualityReleaseGateRef],
    stability_runs: list[QualityReleaseStabilityRun],
    failure: QualityReleaseFailureType,
    missing: str,
) -> QualityReleaseReport:
    return QualityReleaseReport(
        id=f"quality-release-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        thresholds_ref=manifest.thresholds.id,
        quality_gate_refs=[item.id for item in quality_gates],
        stability_run_refs=[item.id for item in stability_runs],
        observed_quality_gate_count=len(quality_gates),
        stability_run_count=len(stability_runs),
        failure_report_refs=[f"failure:{manifest.id}:{failure.value}"],
        missing_ref_fields=[missing],
        failure_type=failure,
        diagnostics=[f"quality release blocked by scenario: {failure.value}"],
        release_decision=QualityReleaseDecision.BLOCKED,
        completion_result=CompletenessResult.FAIL,
    )


def _record_report_event(
    manifest_id: str,
    report: QualityReleaseReport,
    store: ProductionPersistenceStore,
) -> QualityReleaseReport:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:quality-release-report",
        command_type="record_quality_release_report",
        target_aggregate_type="QualityReleaseReport",
        target_aggregate_id=report.id,
        event_type="quality_release_reported",
        output_refs=[report.id],
        policy_decision_refs=report.policy_decision_refs,
        store=store,
    )
    return report.model_copy(
        update={
            "command_record_refs": sorted(set(report.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(report.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(report.outbox_refs + [outbox_ref])),
        }
    )


def _record_event(
    *,
    manifest_id: str,
    command_id: str,
    command_type: str,
    target_aggregate_type: str,
    target_aggregate_id: str,
    event_type: str,
    output_refs: list[Ref],
    policy_decision_refs: list[Ref],
    store: ProductionPersistenceStore,
) -> tuple[Ref, Ref, Ref]:
    command = create_runtime_command(
        command_id=command_id,
        command_type=command_type,
        target_aggregate_type=target_aggregate_type,
        target_aggregate_id=target_aggregate_id,
        actor_ref="actor:quality-release-gate",
        payload_ref=f"payload:{command_id}",
        policy_decision_refs=policy_decision_refs,
    )
    record, _, outbox, _, _ = store.handle_command_once(
        command,
        run_ref=f"run:{manifest_id}",
        objective_ref=f"objective:{manifest_id}",
        plan_ref=f"plan:{manifest_id}",
        event_type=event_type,
        output_refs=output_refs,
    )
    store.mark_outbox_dispatched(
        outbox.id,
        dispatched_at_ref=f"clock:{command_id}:dispatched",
    )
    cursor = store.build_event_cursor(f"run:{manifest_id}")
    return record.id, cursor.id, outbox.id


def _stability_variance(values: list[float]) -> float:
    if not values:
        return 1.0
    average = sum(values) / len(values)
    if average == 0:
        return 1.0
    return (max(values) - min(values)) / average


def _collect(field_name: str, items: Iterable[object]) -> list[Ref]:
    refs: list[Ref] = []
    for item in items:
        refs.extend(getattr(item, field_name))
    return sorted(set(refs))


def _collect_one(field_name: str, items: Iterable[object]) -> list[Ref]:
    return sorted({ref for item in items if (ref := getattr(item, field_name))})
