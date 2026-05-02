from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import (
    CompletenessResult,
    CrossScopeTunnelStatus,
    MemoryEventStatus,
    MemoryPromptUse,
    MemoryTrustLevel,
    MemoryType,
)
from veracrawl.contracts.memory import (
    CrossScopeMemoryTunnel,
    MemoryEvent,
    MemoryKernelReport,
    MemoryRetrievalTrace,
)


def test_memory_event_requires_policy_provenance_and_sanitized_context() -> None:
    event = MemoryEvent(
        id="memory-event:unit",
        run_ref="run:unit",
        scope_ref="scope:unit",
        memory_type=MemoryType.SITE_BEHAVIOR,
        content_ref="memory-content:unit",
        evidence_refs=["evidence:unit"],
        provenance_refs=["published-output:unit"],
        trust_level=MemoryTrustLevel.DERIVED,
        promotion_policy_ref="promotion-policy:unit",
        poisoning_check_ref="poisoning-check:unit",
        sanitized_context_ref="sanitized-context:unit",
        allowed_prompt_use=MemoryPromptUse.SANITIZED_SUMMARY,
        freshness_ref="freshness:unit",
        status=MemoryEventStatus.ACTIVE,
        policy_decision_refs=["policy:unit:memory"],
    )
    assert event.allowed_prompt_use == MemoryPromptUse.SANITIZED_SUMMARY
    with pytest.raises(ValidationError):
        MemoryEvent(
            id="memory-event:bad",
            run_ref="run:bad",
            scope_ref="scope:bad",
            memory_type=MemoryType.SITE_BEHAVIOR,
            content_ref="memory-content:bad",
            provenance_refs=["published-output:bad"],
            trust_level=MemoryTrustLevel.DERIVED,
            promotion_policy_ref="promotion-policy:bad",
            poisoning_check_ref="poisoning-check:bad",
            allowed_prompt_use=MemoryPromptUse.SANITIZED_SUMMARY,
            freshness_ref="freshness:bad",
            status=MemoryEventStatus.ACTIVE,
            policy_decision_refs=["policy:bad:memory"],
        )


def test_retrieval_trace_records_exclusions() -> None:
    trace = MemoryRetrievalTrace(
        id="memory-retrieval:unit",
        run_ref="run:unit",
        query_ref="query:unit",
        scope_ref="scope:unit",
        excluded_memory_refs=["memory-event:invalidated"],
        exclusion_reasons=["invalidated_memory_excluded"],
        policy_decision_refs=["policy:unit:memory"],
        freshness_cutoff_ref="freshness-cutoff:unit",
        retrieval_index_ref="memory-index:unit",
        completion_result=CompletenessResult.PASS,
    )
    assert trace.excluded_memory_refs


def test_approved_cross_scope_tunnel_requires_authorization() -> None:
    with pytest.raises(ValidationError):
        CrossScopeMemoryTunnel(
            id="cross-scope-memory-tunnel:bad",
            source_scope_ref="scope:source",
            target_scope_ref="scope:target",
            allowed_memory_types=[MemoryType.SITE_BEHAVIOR],
            policy_decision_refs=["policy:bad:memory"],
            status=CrossScopeTunnelStatus.APPROVED,
        )


def test_memory_report_pass_requires_replay_refs() -> None:
    with pytest.raises(ValidationError):
        MemoryKernelReport(
            id="memory-kernel-report:bad",
            run_ref="run:bad",
            operator_status="memory_kernel_completed",
            completion_result=CompletenessResult.PASS,
        )
