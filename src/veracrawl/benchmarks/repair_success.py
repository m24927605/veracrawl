"""Repair success rate benchmark runtime."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    RepairBenchmarkFailureType,
    RepairCaseType,
    RepairOutcome,
)
from veracrawl.contracts.repair_success import (
    RepairAttemptTrace,
    RepairQualityManifest,
    RepairQualityReport,
    SeededRepairCase,
)
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.control.runtime import create_runtime_command


@dataclass(frozen=True)
class RepairSuccessBenchmarkResult:
    report: RepairQualityReport
    seeded_cases: list[SeededRepairCase]
    repair_attempts: list[RepairAttemptTrace]


_DIRECT_FAILURES: dict[str, tuple[RepairBenchmarkFailureType, str]] = {
    "repair-success-low-rate": (
        RepairBenchmarkFailureType.SUCCESS_RATE_BELOW_THRESHOLD,
        "repair_success_rate",
    ),
    "repair-success-unsafe-bypass": (
        RepairBenchmarkFailureType.UNSAFE_BYPASS_DETECTED,
        "unsafe_bypass_count",
    ),
    "repair-success-owner-service-bypass": (
        RepairBenchmarkFailureType.OWNER_SERVICE_BYPASS,
        "owner_service_command_refs",
    ),
    "repair-success-model-only-evidence": (
        RepairBenchmarkFailureType.MODEL_ONLY_EVIDENCE,
        "after_evidence_refs",
    ),
    "repair-success-missing-trace": (
        RepairBenchmarkFailureType.MISSING_TRACE_REFS,
        "model_call_trace_refs",
    ),
    "repair-success-rollback-missing": (
        RepairBenchmarkFailureType.MISSING_ROLLBACK_REFS,
        "rollback_refs",
    ),
    "repair-success-unresolved-hidden": (
        RepairBenchmarkFailureType.UNRESOLVED_CRITICAL_REPAIR,
        "critical_unresolved_count",
    ),
    "repair-success-replay-missing": (
        RepairBenchmarkFailureType.MISSING_REPLAY_REFS,
        "replay_bundle_refs",
    ),
}


def run_repair_success_benchmark(
    *,
    manifest: RepairQualityManifest,
    profile: str,
    store: ProductionPersistenceStore,
) -> RepairSuccessBenchmarkResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"repair quality fixture {manifest.id} does not support {profile}")

    seeded_cases = _generate_cases(manifest)
    repair_attempts = _generate_attempts(manifest.id, seeded_cases)
    if manifest.scenario in _DIRECT_FAILURES:
        failure, missing = _DIRECT_FAILURES[manifest.scenario]
        report = _direct_failure_report(manifest, seeded_cases, repair_attempts, failure, missing)
        store.save_canonical_model("repair_quality_reports", report.id, report)
        return RepairSuccessBenchmarkResult(
            report=report,
            seeded_cases=seeded_cases,
            repair_attempts=repair_attempts,
        )

    seeded_cases = [
        _record_case_event(manifest.id, case, store) for case in seeded_cases
    ]
    repair_attempts = [
        _record_attempt_event(manifest.id, attempt, store)
        for attempt in _generate_attempts(manifest.id, seeded_cases)
    ]
    report = _build_report(manifest, seeded_cases, repair_attempts)
    store.save_canonical_model("repair_quality_reports", report.id, report)
    report = _record_report_event(manifest.id, report, store)
    store.save_canonical_model("repair_quality_reports", report.id, report)
    return RepairSuccessBenchmarkResult(
        report=report,
        seeded_cases=seeded_cases,
        repair_attempts=repair_attempts,
    )


def _generate_cases(manifest: RepairQualityManifest) -> list[SeededRepairCase]:
    specs = [
        (RepairOutcome.REPAIRED, manifest.generated_repaired_count, True),
        (
            RepairOutcome.ROLLBACK_APPLIED,
            manifest.generated_rollback_applied_count,
            True,
        ),
        (RepairOutcome.FAILED_SAFE, manifest.generated_failed_safe_count, True),
        (RepairOutcome.ESCALATED, manifest.generated_escalated_count, True),
        (
            RepairOutcome.NON_REPAIRABLE_POLICY,
            manifest.generated_non_repairable_policy_count,
            False,
        ),
        (RepairOutcome.FAILED_UNSAFE, manifest.generated_failed_unsafe_count, True),
    ]
    cases: list[SeededRepairCase] = []
    index = 1
    for outcome, count, repairable in specs:
        for _ in range(count):
            cases.append(_generated_case(manifest.id, index, outcome, repairable))
            index += 1
    return cases


def _generated_case(
    fixture_id: str,
    index: int,
    outcome: RepairOutcome,
    repairable: bool,
) -> SeededRepairCase:
    case_id = f"repair-case:{fixture_id}:{index:04d}"
    return SeededRepairCase(
        id=case_id,
        failure_family=list(RepairCaseType)[(index - 1) % len(RepairCaseType)],
        repairable=repairable,
        critical=index % 5 == 0 and outcome not in {RepairOutcome.ESCALATED},
        expected_outcome=outcome,
        input_artifact_refs=[f"artifact:repair-input:{fixture_id}:{index:04d}"],
        before_evidence_refs=[f"evidence:before:{fixture_id}:{index:04d}"],
        policy_decision_refs=[f"policy:repair:{fixture_id}:{index:04d}"],
        command_record_refs=[f"command:repair-seed:{fixture_id}:{index:04d}"],
        event_cursor_refs=[f"event-cursor:repair-seed:{fixture_id}:{index:04d}"],
        outbox_refs=[f"outbox:repair-seed:{fixture_id}:{index:04d}"],
        replay_bundle_ref=f"replay-bundle:repair-case:{fixture_id}:{index:04d}",
        oracle_ref=f"repair-oracle:{fixture_id}:{index:04d}",
    )


def _generate_attempts(
    fixture_id: str,
    seeded_cases: list[SeededRepairCase],
) -> list[RepairAttemptTrace]:
    return [
        _generated_attempt(fixture_id, index, case)
        for index, case in enumerate(seeded_cases, start=1)
    ]


def _generated_attempt(
    fixture_id: str,
    index: int,
    case: SeededRepairCase,
) -> RepairAttemptTrace:
    attempt_id = f"repair-attempt:{fixture_id}:{index:04d}"
    after_refs = []
    rollback_refs = []
    escalation_refs = []
    if case.expected_outcome in {RepairOutcome.REPAIRED, RepairOutcome.ROLLBACK_APPLIED}:
        after_refs = [f"evidence:after:{fixture_id}:{index:04d}"]
    if case.expected_outcome == RepairOutcome.ROLLBACK_APPLIED:
        rollback_refs = [f"rollback:repair:{fixture_id}:{index:04d}"]
    if case.expected_outcome == RepairOutcome.ESCALATED:
        escalation_refs = [f"escalation:repair:{fixture_id}:{index:04d}"]
    return RepairAttemptTrace(
        id=attempt_id,
        case_ref=case.id,
        outcome=case.expected_outcome,
        model_call_trace_refs=[f"model-call:repair:{fixture_id}:{index:04d}"],
        agent_action_trace_refs=[f"agent-action:repair:{fixture_id}:{index:04d}"],
        tool_call_trace_refs=[f"tool-call:repair:{fixture_id}:{index:04d}"],
        context_bundle_trace_refs=[f"context-bundle:repair:{fixture_id}:{index:04d}"],
        owner_service_command_refs=[f"owner-command:repair:{fixture_id}:{index:04d}"],
        policy_decision_refs=case.policy_decision_refs,
        before_evidence_refs=case.before_evidence_refs,
        after_evidence_refs=after_refs,
        rollback_refs=rollback_refs,
        escalation_refs=escalation_refs,
        command_record_refs=[f"command:repair-attempt:{fixture_id}:{index:04d}"],
        event_cursor_refs=[f"event-cursor:repair-attempt:{fixture_id}:{index:04d}"],
        outbox_refs=[f"outbox:repair-attempt:{fixture_id}:{index:04d}"],
        replay_bundle_ref=f"replay-bundle:repair-attempt:{fixture_id}:{index:04d}",
        token_count=350 + index,
        cost_usd=round(0.003 + (index * 0.0001), 6),
        latency_ms=1200 + (index * 17),
    )


def _record_case_event(
    manifest_id: str,
    case: SeededRepairCase,
    store: ProductionPersistenceStore,
) -> SeededRepairCase:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{case.id}",
        command_type="record_seeded_repair_case",
        target_aggregate_type="SeededRepairCase",
        target_aggregate_id=case.id,
        event_type="seeded_repair_case_recorded",
        output_refs=[case.id],
        policy_decision_refs=case.policy_decision_refs,
        store=store,
    )
    updated = case.model_copy(
        update={
            "command_record_refs": sorted(set(case.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(case.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(case.outbox_refs + [outbox_ref])),
        }
    )
    store.save_canonical_model("seeded_repair_cases", updated.id, updated)
    return updated


def _record_attempt_event(
    manifest_id: str,
    attempt: RepairAttemptTrace,
    store: ProductionPersistenceStore,
) -> RepairAttemptTrace:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{attempt.id}",
        command_type="record_repair_attempt_trace",
        target_aggregate_type="RepairAttemptTrace",
        target_aggregate_id=attempt.id,
        event_type="repair_attempt_trace_recorded",
        output_refs=[attempt.id],
        policy_decision_refs=attempt.policy_decision_refs,
        store=store,
    )
    updated = attempt.model_copy(
        update={
            "command_record_refs": sorted(set(attempt.command_record_refs + [command_ref])),
            "event_cursor_refs": sorted(set(attempt.event_cursor_refs + [event_ref])),
            "outbox_refs": sorted(set(attempt.outbox_refs + [outbox_ref])),
        }
    )
    store.save_canonical_model("repair_attempt_traces", updated.id, updated)
    return updated


def _build_report(
    manifest: RepairQualityManifest,
    seeded_cases: list[SeededRepairCase],
    repair_attempts: list[RepairAttemptTrace],
) -> RepairQualityReport:
    repairable_cases = [case for case in seeded_cases if case.repairable]
    successful_outcomes = {RepairOutcome.REPAIRED, RepairOutcome.ROLLBACK_APPLIED}
    repaired_count = sum(1 for item in repair_attempts if item.outcome in successful_outcomes)
    unsafe_bypass_count = sum(1 for item in repair_attempts if item.unsafe_bypass)
    critical_unresolved_count = _critical_unresolved_count(seeded_cases, repair_attempts)
    repairable_count = len(repairable_cases)
    failure_type, diagnostics, missing = _threshold_failure(
        manifest,
        repair_success_rate=_safe_rate(repaired_count, repairable_count),
        unsafe_bypass_rate=_safe_rate(unsafe_bypass_count, len(repair_attempts)),
        unresolved_critical_rate=_safe_rate(critical_unresolved_count, repairable_count),
    )
    passing = failure_type is None
    return RepairQualityReport(
        id=f"repair-quality-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        thresholds_ref=manifest.thresholds.id,
        seeded_case_refs=[item.id for item in seeded_cases],
        repair_attempt_refs=[item.id for item in repair_attempts],
        repairable_case_count=repairable_count,
        repaired_case_count=repaired_count,
        non_repairable_policy_count=_outcome_count(
            repair_attempts,
            RepairOutcome.NON_REPAIRABLE_POLICY,
        ),
        escalated_count=_outcome_count(repair_attempts, RepairOutcome.ESCALATED),
        rollback_applied_count=_outcome_count(
            repair_attempts,
            RepairOutcome.ROLLBACK_APPLIED,
        ),
        failed_safe_count=_outcome_count(repair_attempts, RepairOutcome.FAILED_SAFE),
        failed_unsafe_count=_outcome_count(repair_attempts, RepairOutcome.FAILED_UNSAFE),
        critical_unresolved_count=critical_unresolved_count,
        unsafe_bypass_count=unsafe_bypass_count,
        repair_success_rate=_safe_rate(repaired_count, repairable_count),
        unsafe_bypass_rate=_safe_rate(unsafe_bypass_count, len(repair_attempts)),
        unresolved_critical_rate=_safe_rate(critical_unresolved_count, repairable_count),
        total_token_count=sum(item.token_count for item in repair_attempts),
        total_cost_usd=round(sum(item.cost_usd for item in repair_attempts), 6),
        p95_latency_ms=_p95([item.latency_ms for item in repair_attempts]),
        model_call_trace_refs=_collect("model_call_trace_refs", repair_attempts),
        agent_action_trace_refs=_collect("agent_action_trace_refs", repair_attempts),
        tool_call_trace_refs=_collect("tool_call_trace_refs", repair_attempts),
        context_bundle_trace_refs=_collect("context_bundle_trace_refs", repair_attempts),
        owner_service_command_refs=_collect("owner_service_command_refs", repair_attempts),
        before_evidence_refs=_collect("before_evidence_refs", repair_attempts),
        after_evidence_refs=_collect("after_evidence_refs", repair_attempts),
        rollback_refs=_collect("rollback_refs", repair_attempts),
        escalation_refs=_collect("escalation_refs", repair_attempts),
        policy_decision_refs=_collect("policy_decision_refs", repair_attempts),
        command_record_refs=_collect("command_record_refs", repair_attempts),
        event_cursor_refs=_collect("event_cursor_refs", repair_attempts),
        outbox_refs=_collect("outbox_refs", repair_attempts),
        replay_bundle_refs=_collect_one("replay_bundle_ref", repair_attempts)
        + _collect_one("replay_bundle_ref", seeded_cases),
        failure_report_refs=[f"failure:{manifest.id}:{failure_type.value}"]
        if failure_type
        else [],
        missing_ref_fields=missing,
        failure_type=failure_type,
        diagnostics=diagnostics,
        operator_status=failure_type.value if failure_type else "repair_quality_completed",
        completion_result=CompletenessResult.PASS if passing else CompletenessResult.FAIL,
    )


def _threshold_failure(
    manifest: RepairQualityManifest,
    *,
    repair_success_rate: float,
    unsafe_bypass_rate: float,
    unresolved_critical_rate: float,
) -> tuple[RepairBenchmarkFailureType | None, list[str], list[str]]:
    if repair_success_rate < manifest.thresholds.min_repair_success_rate:
        return (
            RepairBenchmarkFailureType.SUCCESS_RATE_BELOW_THRESHOLD,
            ["repair success rate below threshold"],
            ["repair_success_rate"],
        )
    if unsafe_bypass_rate > manifest.thresholds.max_unsafe_bypass_rate:
        return (
            RepairBenchmarkFailureType.UNSAFE_BYPASS_DETECTED,
            ["unsafe repair bypass detected"],
            ["unsafe_bypass_count"],
        )
    if unresolved_critical_rate > manifest.thresholds.max_unresolved_critical_rate:
        return (
            RepairBenchmarkFailureType.UNRESOLVED_CRITICAL_REPAIR,
            ["unresolved critical repair detected"],
            ["critical_unresolved_count"],
        )
    return None, [], []


def _direct_failure_report(
    manifest: RepairQualityManifest,
    seeded_cases: list[SeededRepairCase],
    repair_attempts: list[RepairAttemptTrace],
    failure: RepairBenchmarkFailureType,
    missing: str,
) -> RepairQualityReport:
    return RepairQualityReport(
        id=f"repair-quality-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        thresholds_ref=manifest.thresholds.id,
        seeded_case_refs=[item.id for item in seeded_cases],
        repair_attempt_refs=[item.id for item in repair_attempts],
        repairable_case_count=sum(1 for item in seeded_cases if item.repairable),
        repaired_case_count=_outcome_count(repair_attempts, RepairOutcome.REPAIRED)
        + _outcome_count(repair_attempts, RepairOutcome.ROLLBACK_APPLIED),
        failure_report_refs=[f"failure:{manifest.id}:{failure.value}"],
        missing_ref_fields=[missing],
        failure_type=failure,
        diagnostics=[f"repair quality blocked by scenario: {failure.value}"],
        operator_status=failure.value,
        completion_result=CompletenessResult.FAIL,
    )


def _record_report_event(
    manifest_id: str,
    report: RepairQualityReport,
    store: ProductionPersistenceStore,
) -> RepairQualityReport:
    command_ref, event_ref, outbox_ref = _record_event(
        manifest_id=manifest_id,
        command_id=f"cmd:{manifest_id}:repair-quality-report",
        command_type="record_repair_quality_report",
        target_aggregate_type="RepairQualityReport",
        target_aggregate_id=report.id,
        event_type="repair_quality_reported",
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
        actor_ref="actor:repair-quality-benchmark",
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


def _critical_unresolved_count(
    seeded_cases: list[SeededRepairCase],
    repair_attempts: list[RepairAttemptTrace],
) -> int:
    cases_by_ref = {item.id: item for item in seeded_cases}
    unresolved = {RepairOutcome.ESCALATED, RepairOutcome.FAILED_SAFE, RepairOutcome.FAILED_UNSAFE}
    return sum(
        1
        for attempt in repair_attempts
        if cases_by_ref[attempt.case_ref].critical and attempt.outcome in unresolved
    )


def _outcome_count(items: Iterable[RepairAttemptTrace], outcome: RepairOutcome) -> int:
    return sum(1 for item in items if item.outcome == outcome)


def _safe_rate(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _p95(values: list[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) * 0.95) - 1)))
    return ordered[index]


def _collect(field_name: str, items: Iterable[object]) -> list[Ref]:
    refs: list[Ref] = []
    for item in items:
        refs.extend(getattr(item, field_name))
    return sorted(set(refs))


def _collect_one(field_name: str, items: Iterable[object]) -> list[Ref]:
    return sorted({ref for item in items if (ref := getattr(item, field_name))})
