"""Deterministic memory kernel fixture runtime."""

from __future__ import annotations

from dataclasses import dataclass

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    CrossScopeTunnelStatus,
    MemoryEventStatus,
    MemoryFailureType,
    MemoryPromptUse,
    MemoryTrustLevel,
    MemoryType,
)
from veracrawl.contracts.memory import (
    CrossScopeMemoryTunnel,
    MemoryEvent,
    MemoryKernelReport,
    MemoryRetrievalTrace,
    OperationalTemporalMemoryRecord,
)


@dataclass(frozen=True)
class MemoryKernelResult:
    memory_events: list[MemoryEvent]
    retrieval_trace: MemoryRetrievalTrace | None
    tunnel: CrossScopeMemoryTunnel | None
    operational_records: list[OperationalTemporalMemoryRecord]
    report: MemoryKernelReport


def run_memory_kernel(
    *,
    fixture_id: str,
    scenario: str,
    evidence_refs: list[Ref] | None = None,
    policy_decision_refs: list[Ref] | None = None,
) -> MemoryKernelResult:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:memory"]
    evidence = evidence_refs or [f"evidence-packet:{fixture_id}:accepted"]
    if scenario == "poisoned-memory-blocked":
        return _failure_result(
            fixture_id=fixture_id,
            failure=MemoryFailureType.TAINTED_MEMORY_FOR_PROMPT,
            policy_refs=policy_refs,
        )
    if scenario == "unauthorized-cross-scope-memory":
        return _failure_result(
            fixture_id=fixture_id,
            failure=MemoryFailureType.UNAUTHORIZED_CROSS_SCOPE_TUNNEL,
            policy_refs=policy_refs,
        )
    if scenario == "memory-as-evidence":
        return _failure_result(
            fixture_id=fixture_id,
            failure=MemoryFailureType.MEMORY_AS_EVIDENCE,
            policy_refs=policy_refs,
            missing_fields=[MemoryFailureType.MISSING_REANCHOR_EVIDENCE.value],
        )

    tunnel = (
        _tunnel_for(fixture_id, policy_refs)
        if scenario == "cross-scope-sanitized-memory"
        else None
    )
    memory_event = _memory_event_for(
        fixture_id=fixture_id,
        evidence_refs=evidence,
        policy_refs=policy_refs,
        status=(
            MemoryEventStatus.INVALIDATED
            if scenario == "memory-invalidation-exclusion"
            else MemoryEventStatus.ACTIVE
        ),
        allowed_prompt_use=MemoryPromptUse.SANITIZED_SUMMARY,
        taint_labels=[],
    )
    retrieved_refs = [memory_event.id]
    excluded_refs: list[Ref] = []
    exclusion_reasons: list[str] = []
    if scenario == "memory-invalidation-exclusion":
        retrieved_refs = []
        excluded_refs = [memory_event.id]
        exclusion_reasons = ["invalidated_memory_excluded"]
    retrieval_trace = MemoryRetrievalTrace(
        id=f"memory-retrieval-trace:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        query_ref=f"memory-query:{fixture_id}:planning",
        scope_ref=f"scope:{fixture_id}:site",
        retrieved_memory_refs=retrieved_refs,
        excluded_memory_refs=excluded_refs,
        exclusion_reasons=exclusion_reasons,
        policy_decision_refs=policy_refs,
        cross_scope_tunnel_ref=tunnel.id if tunnel else None,
        taint_labels=[],
        freshness_cutoff_ref=f"freshness-cutoff:{fixture_id}:memory",
        retrieval_index_ref=f"memory-index:{fixture_id}:deterministic",
        sanitized_context_ref=f"sanitized-context:{fixture_id}:memory",
        completion_result=CompletenessResult.PASS,
    )
    operational_record = OperationalTemporalMemoryRecord(
        id=f"operational-memory-record:{fixture_id}:1",
        run_ref=f"run:{fixture_id}",
        scope_ref=f"scope:{fixture_id}:site",
        memory_type=memory_event.memory_type,
        memory_event_refs=[memory_event.id],
        valid_from_ref=f"valid-from:{fixture_id}:observed",
        valid_to_ref=f"valid-to:{fixture_id}:invalidated"
        if memory_event.status == MemoryEventStatus.INVALIDATED
        else None,
        evidence_refs=evidence,
        status=memory_event.status,
    )
    report = MemoryKernelReport(
        id=f"memory-kernel-report:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        memory_event_refs=[memory_event.id],
        retrieval_trace_ref=retrieval_trace.id,
        tunnel_ref=tunnel.id if tunnel else None,
        operational_record_refs=[operational_record.id],
        policy_decision_refs=policy_refs,
        command_record_refs=[f"command-record:{fixture_id}:memory"],
        event_cursor_refs=[f"event-cursor:{fixture_id}:memory"],
        outbox_refs=[f"outbox:{fixture_id}:memory"],
        operator_status="memory_kernel_completed",
        completion_result=CompletenessResult.PASS,
    )
    return MemoryKernelResult(
        memory_events=[memory_event],
        retrieval_trace=retrieval_trace,
        tunnel=tunnel,
        operational_records=[operational_record],
        report=report,
    )


def _memory_event_for(
    *,
    fixture_id: str,
    evidence_refs: list[Ref],
    policy_refs: list[Ref],
    status: MemoryEventStatus,
    allowed_prompt_use: MemoryPromptUse,
    taint_labels: list[str],
) -> MemoryEvent:
    return MemoryEvent(
        id=f"memory-event:{fixture_id}:site-behavior",
        run_ref=f"run:{fixture_id}",
        scope_ref=f"scope:{fixture_id}:site",
        memory_type=MemoryType.SITE_BEHAVIOR,
        content_ref=f"memory-content:{fixture_id}:site-behavior",
        evidence_refs=evidence_refs,
        provenance_refs=[f"published-output:{fixture_id}:verified"],
        trust_level=MemoryTrustLevel.DERIVED,
        taint_labels=taint_labels,
        promotion_policy_ref=f"promotion-policy:{fixture_id}:memory",
        poisoning_check_ref=f"poisoning-check:{fixture_id}:passed",
        sanitized_context_ref=f"sanitized-context:{fixture_id}:memory",
        allowed_prompt_use=allowed_prompt_use,
        freshness_ref=f"freshness:{fixture_id}:memory",
        status=status,
        invalidated_by_ref=(
            f"invalidation:{fixture_id}:policy"
            if status == MemoryEventStatus.INVALIDATED
            else None
        ),
        policy_decision_refs=policy_refs,
    )


def _tunnel_for(fixture_id: str, policy_refs: list[Ref]) -> CrossScopeMemoryTunnel:
    return CrossScopeMemoryTunnel(
        id=f"cross-scope-memory-tunnel:{fixture_id}",
        source_scope_ref=f"scope:{fixture_id}:source-project",
        target_scope_ref=f"scope:{fixture_id}:target-project",
        allowed_memory_types=[MemoryType.SITE_BEHAVIOR, MemoryType.FAILURE_REPAIR],
        authorization_ref=f"authorization:{fixture_id}:cross-scope",
        policy_decision_refs=policy_refs,
        sanitized_only=True,
        evidence_ref_required=True,
        taint_exclusion_rules=["exclude_untrusted", "exclude_prompt_forbidden"],
        status=CrossScopeTunnelStatus.APPROVED,
    )


def _failure_result(
    *,
    fixture_id: str,
    failure: MemoryFailureType,
    policy_refs: list[Ref],
    missing_fields: list[str] | None = None,
) -> MemoryKernelResult:
    missing = missing_fields or [failure.value]
    return MemoryKernelResult(
        memory_events=[],
        retrieval_trace=None,
        tunnel=None,
        operational_records=[],
        report=MemoryKernelReport(
            id=f"memory-kernel-report:{fixture_id}",
            run_ref=f"run:{fixture_id}",
            policy_decision_refs=policy_refs,
            failure_report_refs=[f"memory-failure:{fixture_id}:{failure.value}"],
            missing_ref_fields=missing,
            operator_status=failure.value,
            completion_result=CompletenessResult.FAIL,
        ),
    )
