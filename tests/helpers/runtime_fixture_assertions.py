from __future__ import annotations

from pathlib import Path

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.control.runtime import RuntimeRunReport


def assert_successful_runtime_report(report: RuntimeRunReport) -> None:
    assert report.completion_result == CompletenessResult.PASS
    assert report.published is True
    assert report.published_output_ref
    assert report.output_manifest_ref
    assert report.replay_manifest_ref
    assert report.source_adapter_result_refs
    assert report.artifact_refs
    assert report.normalized_document_refs
    assert report.extraction_candidate_refs
    assert report.evidence_packet_refs
    assert report.verification_decision_refs
    assert not report.missing_replay_ref_fields


def assert_negative_runtime_report(
    report: RuntimeRunReport,
    *,
    operator_status: str,
    completion_result: CompletenessResult | None = None,
) -> None:
    assert report.published is False
    assert report.published_output_ref is None
    assert report.output_manifest_ref is None
    assert report.operator_status == operator_status
    assert report.blocking_gate_ref
    if completion_result is not None:
        assert report.completion_result == completion_result


def runtime_fixture_path(root: Path, fixture_id: str) -> Path:
    return root / "tests" / "fixtures" / fixture_id
