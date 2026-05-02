from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.memory.kernel import run_memory_kernel


def test_memory_as_evidence_is_rejected_and_requires_reanchor() -> None:
    result = run_memory_kernel(
        fixture_id="unit-memory-evidence",
        scenario="memory-as-evidence",
        policy_decision_refs=["policy:unit:memory"],
    )
    assert result.report.completion_result == CompletenessResult.FAIL
    assert result.report.operator_status == "memory_as_evidence"
    assert "missing_reanchor_evidence" in result.report.missing_ref_fields
