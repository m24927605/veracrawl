from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult, MemoryEventStatus
from veracrawl.memory.kernel import run_memory_kernel


def test_memory_kernel_writes_retrieves_and_records_operational_memory() -> None:
    result = run_memory_kernel(
        fixture_id="unit-memory",
        scenario="memory-write-retrieve-success",
        evidence_refs=["evidence:unit"],
        policy_decision_refs=["policy:unit:memory"],
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert result.memory_events
    assert result.retrieval_trace
    assert result.retrieval_trace.retrieved_memory_refs == [result.memory_events[0].id]
    assert result.operational_records


def test_memory_invalidation_excludes_memory_from_retrieval() -> None:
    result = run_memory_kernel(
        fixture_id="unit-memory-invalidated",
        scenario="memory-invalidation-exclusion",
        evidence_refs=["evidence:unit"],
        policy_decision_refs=["policy:unit:memory"],
    )
    assert result.report.completion_result == CompletenessResult.PASS
    assert result.memory_events[0].status == MemoryEventStatus.INVALIDATED
    assert result.retrieval_trace
    assert result.retrieval_trace.excluded_memory_refs == [result.memory_events[0].id]
    assert not result.retrieval_trace.retrieved_memory_refs


def test_poisoned_memory_is_blocked_from_prompt_use() -> None:
    result = run_memory_kernel(
        fixture_id="unit-memory-poisoned",
        scenario="poisoned-memory-blocked",
        policy_decision_refs=["policy:unit:memory"],
    )
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.operator_status == "tainted_memory_for_prompt"
