"""Memory replay validation."""

from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.memory import MemoryKernelReport


def missing_memory_replay_refs(report: MemoryKernelReport) -> list[str]:
    required = {
        "memory_event_refs": report.memory_event_refs,
        "retrieval_trace_ref": report.retrieval_trace_ref,
        "operational_record_refs": report.operational_record_refs,
        "policy_decision_refs": report.policy_decision_refs,
        "command_record_refs": report.command_record_refs,
        "event_cursor_refs": report.event_cursor_refs,
        "outbox_refs": report.outbox_refs,
    }
    missing = [name for name, value in required.items() if not value]
    return sorted(set(missing + report.missing_ref_fields))


def memory_replay_passes(report: MemoryKernelReport) -> bool:
    return report.completion_result == CompletenessResult.PASS and not (
        missing_memory_replay_refs(report)
    )
