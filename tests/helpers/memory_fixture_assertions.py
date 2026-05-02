from __future__ import annotations

from veracrawl.cli.memory import MemoryFixtureRunReport
from veracrawl.contracts.enums import CompletenessResult


def assert_memory_success(report: MemoryFixtureRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.operator_status == "memory_kernel_completed"
    assert report.memory_event_refs
    assert report.retrieval_trace_ref
    assert report.operational_record_refs
    assert report.policy_decision_refs
    assert report.command_record_refs
    assert report.event_cursor_refs
    assert report.outbox_refs


def assert_memory_negative(
    report: MemoryFixtureRunReport,
    *,
    operator_status: str,
) -> None:
    assert report.completion_result == CompletenessResult.FAIL
    assert report.operator_status == operator_status
    assert report.failure_report_refs
    assert report.missing_ref_fields
    assert not report.memory_event_refs
