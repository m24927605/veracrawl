"""Deterministic target crawl runtime runner."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    AgentRecommendationSubject,
    CompletenessResult,
    TargetRuntimeFailureType,
    TargetRuntimeStatus,
    TargetWebsitePattern,
)
from veracrawl.contracts.target_runtime import (
    TargetAIRecommendationRecord,
    TargetCrawlPatternRecord,
    TargetRuntimeReport,
)


@dataclass(frozen=True)
class TargetRuntimeResult:
    pattern_records: list[TargetCrawlPatternRecord]
    ai_recommendations: list[TargetAIRecommendationRecord]
    report: TargetRuntimeReport


_TARGET_PATTERNS: tuple[TargetWebsitePattern, ...] = (
    TargetWebsitePattern.STATIC,
    TargetWebsitePattern.SITEMAP_RSS_FEED,
    TargetWebsitePattern.LISTING_DETAIL,
    TargetWebsitePattern.API_LIKE_ENDPOINTS,
    TargetWebsitePattern.DOCUMENTS,
    TargetWebsitePattern.DRIFTED_SITES,
    TargetWebsitePattern.JAVASCRIPT_PAGES,
)

_FAILURES: dict[str, tuple[TargetRuntimeStatus, TargetRuntimeFailureType, str]] = {
    "target-runtime-policy-denied": (
        TargetRuntimeStatus.BLOCKED,
        TargetRuntimeFailureType.POLICY_DENIED,
        "source access denied by target runtime policy",
    ),
    "target-runtime-prompt-injection": (
        TargetRuntimeStatus.BLOCKED,
        TargetRuntimeFailureType.PROMPT_INJECTION,
        "untrusted source content attempted to override trusted crawl policy",
    ),
    "target-runtime-missing-evidence": (
        TargetRuntimeStatus.FAILED,
        TargetRuntimeFailureType.MISSING_EVIDENCE,
        "accepted output cannot be linked to required source evidence",
    ),
    "target-runtime-replay-mismatch": (
        TargetRuntimeStatus.FAILED,
        TargetRuntimeFailureType.REPLAY_MISMATCH,
        "replay event sequence does not match target runtime oracle",
    ),
    "target-runtime-partial-export": (
        TargetRuntimeStatus.FAILED,
        TargetRuntimeFailureType.PARTIAL_EXPORT,
        "export receipt set is incomplete for accepted outputs",
    ),
    "target-runtime-false-complete": (
        TargetRuntimeStatus.FAILED,
        TargetRuntimeFailureType.FALSE_COMPLETE,
        "run attempted to mark degraded capability complete",
    ),
}


def run_target_runtime_fixture(
    *,
    fixture_id: str,
    scenario: str,
    profile: str = "target",
) -> TargetRuntimeResult:
    if profile != "target":
        raise ValueError(f"unsupported target runtime profile: {profile}")
    if scenario == "target-runtime-needs-review":
        return _needs_review_result(fixture_id)
    if scenario in _FAILURES:
        status, failure, diagnostic = _FAILURES[scenario]
        return _failure_result(
            fixture_id=fixture_id,
            status=status,
            failure=failure,
            diagnostic=diagnostic,
        )
    repaired = scenario == "target-runtime-drift-repair"
    return _success_result(fixture_id=fixture_id, repaired=repaired)


def _success_result(*, fixture_id: str, repaired: bool) -> TargetRuntimeResult:
    run_ref = _run_ref(fixture_id)
    policy_refs = _policy_refs(fixture_id)
    command_refs = _command_refs(fixture_id)
    event_refs = _event_refs(fixture_id)
    outbox_refs = _outbox_refs(fixture_id)
    replay_ref = _replay_ref(fixture_id)
    pattern_records = [
        _pattern_record(
            fixture_id=fixture_id,
            pattern=pattern,
            policy_refs=policy_refs,
            command_refs=command_refs,
            event_refs=event_refs,
            outbox_refs=outbox_refs,
            replay_ref=replay_ref,
        )
        for pattern in _TARGET_PATTERNS
    ]
    ai = _accepted_ai_recommendation(
        fixture_id=fixture_id,
        subject=(
            AgentRecommendationSubject.REPAIR
            if repaired
            else AgentRecommendationSubject.CRAWL_PLAN
        ),
        repair_refs=(
            [f"frontier:{fixture_id}:drifted_sites:repair-retry"] if repaired else []
        ),
    )
    report = TargetRuntimeReport(
        id=f"target-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=run_ref,
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        status=TargetRuntimeStatus.COMPLETE,
        completion_result=CompletenessResult.PASS,
        covered_patterns=[record.website_pattern for record in pattern_records],
        pattern_record_refs=[record.id for record in pattern_records],
        accepted_output_refs=_collect(pattern_records, "accepted_output_refs"),
        evidence_refs=_collect(pattern_records, "evidence_refs"),
        verification_refs=_collect(pattern_records, "verification_refs"),
        graph_refs=_collect(pattern_records, "graph_refs"),
        export_receipt_refs=[f"export-receipt:{fixture_id}:target"],
        output_manifest_refs=[f"output-manifest:{fixture_id}:target"],
        policy_decision_refs=policy_refs,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_refs,
        artifact_refs=_collect(pattern_records, "artifact_refs"),
        ai_recommendation_refs=[ai.id],
        repair_action_refs=(
            [f"repair-action:{fixture_id}:drifted-sites"] if repaired else []
        ),
        recovery_action_refs=[f"recovery-action:{fixture_id}:operator-visible"],
        privacy_lifecycle_refs=[f"privacy:{fixture_id}:retention-redaction"],
        replay_bundle_ref=replay_ref,
        operator_status=(
            "target_runtime_drift_repaired" if repaired else "target_runtime_completed"
        ),
    )
    return TargetRuntimeResult(pattern_records, [ai], report)


def _needs_review_result(fixture_id: str) -> TargetRuntimeResult:
    policy_refs = _policy_refs(fixture_id)
    ai = _accepted_ai_recommendation(
        fixture_id=fixture_id,
        subject=AgentRecommendationSubject.REPAIR,
        repair_refs=[f"frontier:{fixture_id}:needs-review"],
    )
    report = TargetRuntimeReport(
        id=f"target-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=_run_ref(fixture_id),
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        status=TargetRuntimeStatus.NEEDS_REVIEW,
        completion_result=CompletenessResult.NEEDS_REVIEW,
        policy_decision_refs=policy_refs,
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        ai_recommendation_refs=[ai.id],
        review_item_refs=[f"review:{fixture_id}:evidence-gap"],
        recovery_action_refs=[f"recovery-action:{fixture_id}:rerun-frontier"],
        missing_ref_fields=["accepted_output_refs"],
        diagnostics=["recoverable evidence gap requires operator review"],
        operator_status="target_runtime_needs_review",
    )
    return TargetRuntimeResult([], [ai], report)


def _failure_result(
    *,
    fixture_id: str,
    status: TargetRuntimeStatus,
    failure: TargetRuntimeFailureType,
    diagnostic: str,
) -> TargetRuntimeResult:
    policy_refs = _policy_refs(fixture_id)
    ai = _blocked_ai_recommendation(
        fixture_id=fixture_id,
        subject=(
            AgentRecommendationSubject.REPAIR
            if failure == TargetRuntimeFailureType.PROMPT_INJECTION
            else AgentRecommendationSubject.CRAWL_PLAN
        ),
        blocked_ref=f"blocked-action:{fixture_id}:{failure.value}",
    )
    report = TargetRuntimeReport(
        id=f"target-runtime-report:{fixture_id}",
        fixture_id=fixture_id,
        run_ref=_run_ref(fixture_id),
        objective_ref=f"objective:{fixture_id}",
        plan_ref=f"plan:{fixture_id}",
        status=status,
        completion_result=CompletenessResult.FAIL,
        policy_decision_refs=policy_refs,
        command_record_refs=_command_refs(fixture_id),
        event_cursor_refs=_event_refs(fixture_id),
        outbox_refs=_outbox_refs(fixture_id),
        ai_recommendation_refs=[ai.id],
        failure_type=failure,
        failure_report_refs=[f"failure:{fixture_id}:{failure.value}"],
        missing_ref_fields=_missing_fields_for(failure),
        diagnostics=[diagnostic],
        operator_status=failure.value,
    )
    return TargetRuntimeResult([], [ai], report)


def _pattern_record(
    *,
    fixture_id: str,
    pattern: TargetWebsitePattern,
    policy_refs: list[Ref],
    command_refs: list[Ref],
    event_refs: list[Ref],
    outbox_refs: list[Ref],
    replay_ref: Ref,
) -> TargetCrawlPatternRecord:
    suffix = pattern.value
    return TargetCrawlPatternRecord(
        id=f"target-pattern:{fixture_id}:{suffix}",
        run_ref=_run_ref(fixture_id),
        website_pattern=pattern,
        frontier_item_refs=[f"frontier:{fixture_id}:{suffix}"],
        source_observation_refs=[f"source-observation:{fixture_id}:{suffix}"],
        source_adapter_result_refs=[f"source-result:{fixture_id}:{suffix}"],
        extraction_result_refs=[f"extraction:{fixture_id}:{suffix}"],
        accepted_output_refs=[f"accepted-output:{fixture_id}:{suffix}"],
        evidence_refs=[f"evidence:{fixture_id}:{suffix}"],
        verification_refs=[f"verification:{fixture_id}:{suffix}"],
        graph_refs=[f"graph:{fixture_id}:{suffix}"],
        policy_decision_refs=policy_refs,
        command_record_refs=command_refs,
        event_cursor_refs=event_refs,
        outbox_refs=outbox_refs,
        artifact_refs=[f"artifact:{fixture_id}:{suffix}:raw"],
        replay_refs=[replay_ref, f"replay:{fixture_id}:{suffix}"],
        operator_visible_refs=[f"operator-result:{fixture_id}:{suffix}"],
        pattern_specific_refs=_pattern_specific_refs(fixture_id, pattern),
        result=CompletenessResult.PASS,
    )


def _accepted_ai_recommendation(
    *,
    fixture_id: str,
    subject: AgentRecommendationSubject,
    repair_refs: list[Ref],
) -> TargetAIRecommendationRecord:
    return TargetAIRecommendationRecord(
        id=f"target-ai:{fixture_id}:{subject.value}",
        run_ref=_run_ref(fixture_id),
        subject=subject,
        recommendation_ref=f"agent-recommendation:{fixture_id}:{subject.value}",
        accepted=True,
        policy_decision_refs=[f"policy:{fixture_id}:agent-tool"],
        tool_call_refs=[f"tool-call:{fixture_id}:{subject.value}"],
        trace_refs=[f"agent-trace:{fixture_id}:{subject.value}"],
        repair_frontier_refs=repair_refs,
        result=CompletenessResult.PASS,
    )


def _blocked_ai_recommendation(
    *,
    fixture_id: str,
    subject: AgentRecommendationSubject,
    blocked_ref: Ref,
) -> TargetAIRecommendationRecord:
    return TargetAIRecommendationRecord(
        id=f"target-ai:{fixture_id}:{subject.value}:blocked",
        run_ref=_run_ref(fixture_id),
        subject=subject,
        recommendation_ref=f"agent-recommendation:{fixture_id}:{subject.value}:blocked",
        accepted=False,
        policy_decision_refs=[f"policy:{fixture_id}:agent-tool-denied"],
        blocked_action_refs=[blocked_ref],
        result=CompletenessResult.FAIL,
    )


def _pattern_specific_refs(
    fixture_id: str,
    pattern: TargetWebsitePattern,
) -> dict[str, Ref]:
    suffix = pattern.value
    return {
        "fixture_ref": f"fixture:{fixture_id}:{suffix}",
        "oracle_ref": f"oracle:{fixture_id}:{suffix}",
        "general_pattern_ref": f"pattern:{suffix}",
    }


def _collect(records: list[TargetCrawlPatternRecord], field_name: str) -> list[Ref]:
    values: list[Ref] = []
    for record in records:
        field_value = getattr(record, field_name)
        if isinstance(field_value, list):
            values.extend(field_value)
    return values


def _missing_fields_for(failure: TargetRuntimeFailureType) -> list[str]:
    return {
        TargetRuntimeFailureType.POLICY_DENIED: ["source_policy_refs"],
        TargetRuntimeFailureType.PROMPT_INJECTION: ["trusted_prompt_boundary_ref"],
        TargetRuntimeFailureType.MISSING_EVIDENCE: ["evidence_refs"],
        TargetRuntimeFailureType.REPLAY_MISMATCH: ["replay_bundle_ref"],
        TargetRuntimeFailureType.PARTIAL_EXPORT: ["export_receipt_refs"],
        TargetRuntimeFailureType.FALSE_COMPLETE: ["status_accuracy_refs"],
        TargetRuntimeFailureType.DRIFT_REPAIR_REQUIRED: ["repair_action_refs"],
        TargetRuntimeFailureType.ORACLE_MISMATCH: ["oracle_refs"],
    }[failure]


def _run_ref(fixture_id: str) -> Ref:
    return f"run:{fixture_id}"


def _policy_refs(fixture_id: str) -> list[Ref]:
    return [
        f"policy:{fixture_id}:source",
        f"policy:{fixture_id}:prompt-boundary",
        f"policy:{fixture_id}:publication",
        f"policy:{fixture_id}:export",
    ]


def _command_refs(fixture_id: str) -> list[Ref]:
    return [f"command:{fixture_id}:target-runtime"]


def _event_refs(fixture_id: str) -> list[Ref]:
    return [f"event-cursor:{fixture_id}:target-runtime"]


def _outbox_refs(fixture_id: str) -> list[Ref]:
    return [f"outbox:{fixture_id}:target-runtime"]


def _replay_ref(fixture_id: str) -> Ref:
    return f"replay-bundle:{fixture_id}:target-runtime"
